
from app import app
from models import db, BuildStage, Task

# Add utility tasks to stages 1-19
with app.app_context():
    # Get all areas
    areas = BuildStage.query.all()
    
    for stage in areas:
        # Only add to stages 1-19
        if stage.name.split('-')[0].isdigit():
            stage_num = int(stage.name.split('-')[0])
            if 1 <= stage_num <= 19:
                # Check if task already exists
                existing_task = Task.query.filter_by(
                    stage_id=stage.id,
                    name="Stage materials"
                ).first()
                
                if not existing_task:
                    # Create new task
                    task = Task(
                        stage_id=stage.id,
                        name="Stage materials",
                        description="Utility department task to stage and prepare materials for this build phase",
                        order=0  # Place at beginning of task list
                    )
                    db.session.add(task)
                    print(f"Added utility task to stage: {stage.name}")
    
    # Commit all changes
    db.session.commit()
    print("Utility tasks added successfully")
