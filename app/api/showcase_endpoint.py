from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.engine.result import ScalarResult  # Import for type hint clarity
from datetime import datetime  # Import datetime for fake ID generation
from pydantic import BaseModel
import traceback
import sys
import logging

from app.db.session import get_session
from app.models.showcase_feedback_model import (
    ShowcaseQuestionnaireTemplate,
    ShowcaseFeedback,
    ShowcaseTrainingPlan,
    Waitlist,
)
from app.schemas.showcase_schema import (
    ShowcaseQuestionnaireResponse,
    ShowcaseFeedbackCreate,
    ShowcaseFeedbackUpdate,
    ShowcaseFeedbackResponse,
    ShowcaseTrainingPlanCreate,
    ShowcaseTrainingPlanResponse,
)
from app.schemas.workout_schema import WorkoutSchemaWithBlocks
from app.services.workout_service import get_workout_details, save_workout_to_db_async
from app.llm.chains.workout_generation_chain import generate_workout
from app.llm.schemas.workout_generation_schema import WorkoutSchema
from app.llm.service.run_workout_chain import run_workout_chain

router = APIRouter(prefix="/showcase")


class FeedbackRatingUpdate(BaseModel):
    rating: int


class FeedbackCommentUpdate(BaseModel):
    comment: str


class WaitlistCall(BaseModel):
    email: str


@router.post(
    "/waitlist",
    response_model=WaitlistCall,
    status_code=status.HTTP_201_CREATED,
    summary="Add an email to the waitlist",
    tags=["showcase"],
)
async def join_waitlist(
    *, session: AsyncSession = Depends(get_session), waitlist_data: WaitlistCall
) -> WaitlistCall:
    """
    Adds an email to the waitlist.
    """
    email = waitlist_data.email
    print(f"Adding email to waitlist: {email}")

    db_waitlist = Waitlist(email=waitlist_data.email)

    try:
        session.add(db_waitlist)
        await session.commit()
        await session.refresh(db_waitlist)
    except Exception as e:
        print(f"Error adding email to waitlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to add email to waitlist.")

    print(f"Added email to waitlist: {email}")

    return waitlist_data


@router.get(
    "/questionnaire",
    response_model=ShowcaseQuestionnaireResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific showcase questionnaire template by its string ID",
    tags=["showcase"],
)
async def get_showcase_questionnaire_template(
    *,
    session: AsyncSession = Depends(get_session),
) -> ShowcaseQuestionnaireResponse:
    """
    Retrieve the questions and ID for a specific showcase questionnaire template
    using its unique string identifier (e.g., "q_v1.1").
    """
    logger = logging.getLogger("showcase_endpoint")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    if not logger.hasHandlers():
        logger.addHandler(handler)

    questionnaire_id = "q_v2.1"

    logger.info(f"[questionnaire] Fetching questionnaire template with ID: {questionnaire_id}")

    try:
        statement = select(ShowcaseQuestionnaireTemplate).where(
            ShowcaseQuestionnaireTemplate.questionnaire_id == questionnaire_id
        )
        logger.debug(f"[questionnaire] Executing statement: {statement}")
        result = await session.exec(statement)
        questionnaire_template = result.first()
        logger.info(f"[questionnaire] Query executed. Result: {questionnaire_template}")
    except Exception as e:
        logger.error(f"[questionnaire] Exception during DB query: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching questionnaire template."
        )

    if not questionnaire_template:
        logger.warning(f"[questionnaire] Questionnaire template with ID '{questionnaire_id}' not found in DB.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire template with ID '{questionnaire_id}' not found",
        )
    logger.info(f"[questionnaire] Found questionnaire template: {questionnaire_template.id}")
    return questionnaire_template


# --- Endpoint to create initial feedback (replaces MSW POST /feedback/questionnaire) ---
@router.post(
    "/questionnaire",
    response_model=ShowcaseFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit initial questionnaire answers and create a feedback record",
    tags=["showcase", "feedback"],
)
async def create_showcase_feedback(
    *,
    session: AsyncSession = Depends(get_session),
    feedback_data: ShowcaseFeedbackCreate,
) -> ShowcaseFeedbackResponse:
    """
    Receives questionnaire answers, finds the corresponding template,
    and creates a new ShowcaseFeedback record.
    Returns the created feedback record including its new ID.
    """
    print(
        f"Received feedback data for questionnaireId: {feedback_data.questionnaireId}"
    )

    # 1. Find the Questionnaire Template based on the string ID
    template_statement = select(ShowcaseQuestionnaireTemplate).where(
        ShowcaseQuestionnaireTemplate.questionnaire_id == feedback_data.questionnaireId
    )
    template_result = await session.exec(template_statement)
    questionnaire_template = template_result.first()

    if not questionnaire_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire template with ID '{feedback_data.questionnaireId}' not found",
        )

    # 2. Create the ShowcaseFeedback instance
    db_feedback = ShowcaseFeedback(
        questionnaire_template_id=questionnaire_template.id,
        answers=feedback_data.answers,
        # Other fields like workout_id, assessment, comment are initially null
    )

    # 3. Add, commit, and refresh
    session.add(db_feedback)
    await session.commit()
    await session.refresh(db_feedback)

    print(f"Created ShowcaseFeedback record with ID: {db_feedback.id}")

    # FastAPI automatically uses the response_model to serialize db_feedback
    return db_feedback


# --- Endpoint to update feedback (replaces MSW PUT /feedback/questionnaire/:feedbackId) ---
@router.put(
    "/questionnaire/{feedback_id}",
    response_model=ShowcaseFeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Update questionnaire answers for an existing feedback record",
    tags=["showcase", "feedback"],
)
async def update_showcase_feedback(
    *,
    session: AsyncSession = Depends(get_session),
    feedback_id: int,
    feedback_data: ShowcaseFeedbackUpdate,  # Contains questionnaireId and answers
) -> ShowcaseFeedbackResponse:
    """
    Updates the answers for a specific ShowcaseFeedback record identified by its ID.
    Optionally could verify questionnaireId matches, but primarily updates answers.
    Returns the updated feedback record.
    """
    print(f"Updating feedback record ID: {feedback_id}")

    # 1. Find the existing Feedback record
    feedback_statement = select(ShowcaseFeedback).where(
        ShowcaseFeedback.id == feedback_id
    )
    feedback_result = await session.exec(feedback_statement)
    db_feedback = feedback_result.first()

    if not db_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ShowcaseFeedback record with ID {feedback_id} not found",
        )

    # Optional: Verify the questionnaireId from the request matches the template linked to the feedback
    # This adds complexity but ensures consistency if needed.
    # template = await session.get(ShowcaseQuestionnaireTemplate, db_feedback.questionnaire_template_id)
    # if not template or template.questionnaire_id != feedback_data.questionnaireId:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Questionnaire ID mismatch between request and stored feedback record."
    #     )

    # 2. Update the fields
    db_feedback.answers = feedback_data.answers
    # updated_at will be handled by the database/SQLAlchemy if configured

    # 3. Add, commit, and refresh
    session.add(db_feedback)
    await session.commit()
    await session.refresh(db_feedback)

    print(f"Updated ShowcaseFeedback record with ID: {db_feedback.id}")

    return db_feedback


# --- Endpoint to create a Training Plan and link it to Feedback ---
@router.post(
    "/training-plans",
    response_model=WorkoutSchemaWithBlocks,
    status_code=status.HTTP_201_CREATED,
    summary="Create a showcase training plan and link it (TEMP: returns fake workout)",
    tags=["showcase", "training_plan"],
)
async def create_training_plan(
    *,
    session: AsyncSession = Depends(get_session),
    plan_data: ShowcaseTrainingPlanCreate,
) -> WorkoutSchemaWithBlocks:
    """
    Creates a new ShowcaseTrainingPlan based on the provided data
    and links it to an existing ShowcaseFeedback record using feedbackId.
    """
    try:
        print(
            f"Received request to create training plan and link to feedback ID: {plan_data.feedbackId}"
        )

        # 1. Find the existing Feedback record (optional)
        feedback_record = None
        if plan_data.feedbackId is not None:
            feedback_statement = select(ShowcaseFeedback).where(
                ShowcaseFeedback.id == plan_data.feedbackId
            )
            feedback_result: ScalarResult[ShowcaseFeedback] = await session.exec(
                feedback_statement
            )
            feedback_record: ShowcaseFeedback | None = feedback_result.first()
            if not feedback_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"ShowcaseFeedback record with ID {plan_data.feedbackId} not found. Cannot link training plan.",
                )

        # 3. Create the ShowcaseTrainingPlan instance
        new_plan = ShowcaseTrainingPlan(
            goal=plan_data.goal,
            restrictions=plan_data.restrictions,
            equipment=plan_data.equipment,
            session_duration=plan_data.session_duration,
            history=plan_data.history,
        )

        # 4. Add the new plan to the session
        session.add(new_plan)

        # 5. Flush the session to get the ID of the new plan *before* commit
        await session.flush()
        await session.refresh(new_plan)  # Refresh to get the ID assigned by flush

        if new_plan.id is None:
            # This should ideally not happen after a successful flush
            await session.rollback()  # Rollback changes if ID assignment failed
            raise HTTPException(
                status_code=500, detail="Failed to create training plan ID."
            )

        print(f"Training plan created with temporary ID: {new_plan.id}.")
        
        # 6. Link the new plan ID to the feedback record (if feedbackId was provided)
        feedback_id_for_log = None
        if feedback_record is not None:
            feedback_id_for_log = feedback_record.id
            print(f"Linking training plan to feedback {feedback_id_for_log}")
            feedback_record.training_plan_id = new_plan.id
            session.add(feedback_record)  # Add the modified feedback record back

        # 7. Commit the transaction (saves both the new plan and the updated feedback)
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()  # Rollback on commit error
            print(f"Error during commit: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to save training plan and link feedback."
            )

        # 8. Refresh the plan again after commit (optional but good practice)
        await session.refresh(new_plan)
        if feedback_id_for_log is not None:
            print(
                f"Successfully created training plan {new_plan.id} and linked to feedback {feedback_id_for_log}"
            )
        else:
            print(f"Successfully created training plan {new_plan.id} (no feedback linked)")
        
        
        print("Generating and saving workout via run_workout_chain...")
        
        # turn new_plan into a string
        new_plan_string = new_plan.model_dump_json(indent=2)
        
        
        workout = await run_workout_chain(
            user_id=None,  # Showcase: kein User-Kontext nötig
            user_prompt=new_plan_string,
            db=session,
            save_to_db=False
        )
        
        # put the training_plan_id to Null
        workout.training_plan_id = None
        
        # save the workout to the database
        session.add(workout)
        await session.commit()
        await session.refresh(workout)
        
        workout_id = workout.id  # <-- Sofort extrahieren!

        # Feedback aktualisieren
        if feedback_record is not None:
            try:
                feedback_record.workout_id = workout_id
                session.add(feedback_record)
                await session.commit()
                await session.refresh(feedback_record)
                print(f"Updated feedback record with workout ID: {workout_id}")
            except Exception as e:
                print(f"Error updating feedback record: {e}")
                traceback.print_exc(file=sys.stdout)
                raise HTTPException(
                    status_code=500, detail=f"Failed to update feedback record: {str(e)}"
                )

        # Workout mit Details laden und zurückgeben
        try:
            loaded_workout = await get_workout_details(
                workout_id=workout_id, db=session
            )
            return loaded_workout
        except Exception as e:
            print(f"Error loading workout details: {e}")
            traceback.print_exc(file=sys.stdout)
            raise HTTPException(
                status_code=500, detail=f"Failed to load workout details: {str(e)}"
            )
    except Exception as e:
        print(f"Unhandled exception in create_training_plan: {e}")
        traceback.print_exc(file=sys.stdout)
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


# --- Endpoint to update feedback rating (replaces MSW PUT /feedback/rating/:feedbackId) ---
@router.put(
    "/rating/{feedback_id}",
    response_model=ShowcaseFeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Update the rating for a specific feedback record",
    tags=["showcase", "feedback"],
)
async def update_feedback_rating(
    *,
    session: AsyncSession = Depends(get_session),
    feedback_id: int,
    rating_data: FeedbackRatingUpdate,
) -> ShowcaseFeedbackResponse:
    """
    Updates the rating for a specific ShowcaseFeedback record identified by its ID.
    Returns the updated feedback record.
    """
    rating = rating_data.rating
    print(f"Updating rating for feedback ID: {feedback_id} to {rating}")

    # 1. Find the existing Feedback record
    feedback_statement = select(ShowcaseFeedback).where(
        ShowcaseFeedback.id == feedback_id
    )
    feedback_result = await session.exec(feedback_statement)
    db_feedback = feedback_result.first()

    if not db_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ShowcaseFeedback record with ID {feedback_id} not found",
        )

    # 2. Update the rating
    db_feedback.feedback_rating = rating

    # 3. Add, commit, and refresh
    session.add(db_feedback)
    await session.commit()
    await session.refresh(db_feedback)

    print(f"Updated feedback rating for ID: {feedback_id} to {rating}")

    return db_feedback


@router.put(
    "/comment/{feedback_id}",
    response_model=ShowcaseFeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Update the comment for a specific feedback record",
    tags=["showcase", "feedback"],
)
async def update_feedback_comment(
    *,
    session: AsyncSession = Depends(get_session),
    feedback_id: int,
    comment_data: FeedbackCommentUpdate,
) -> ShowcaseFeedbackResponse:
    """
    Updates the comment for a specific ShowcaseFeedback record identified by its ID.
    Returns the updated feedback record.
    """
    comment = comment_data.comment
    print(f"Updating comment for feedback ID: {feedback_id} to {comment}")

    # 1. Find the existing Feedback record
    feedback_statement = select(ShowcaseFeedback).where(
        ShowcaseFeedback.id == feedback_id
    )
    feedback_result = await session.exec(feedback_statement)
    db_feedback = feedback_result.first()

    if not db_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ShowcaseFeedback record with ID {feedback_id} not found",
        )

    # 2. Update the comment
    db_feedback.feedback_comment = comment

    # 3. Add, commit, and refresh
    session.add(db_feedback)
    await session.commit()
    await session.refresh(db_feedback)

    print(f"Updated feedback comment for ID: {feedback_id} to {comment}")

    return db_feedback
