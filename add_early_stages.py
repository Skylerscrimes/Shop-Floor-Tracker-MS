import os
from datetime import datetime
from flask import Flask
from models import db, Area, BuildStage

# Create Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# List of early build stages to add (1-6)
early_build_stages = [
    "1-Foundation Prep",
    "2-Foundation Pour",
    "3-Floor Framing",
    "4-Wall Framing",
    "5-Roof Framing",
    "6-Roof Covering"
]

# Add build stages to all areas
with app.app_context():
    # Get all areas
    areas = Area.query.all()
    
    print(f"Found {len(areas)} areas in the database")
    
    for area in areas:
        print(f"Adding early stages to {area.area_type}")
        
        # Get existing stages for this area
        existing_stages = [stage.name for stage in BuildStage.query.filter_by(area_id=area.id).all()]
        
        # Add each early build stage
        for i, stage_name in enumerate(early_build_stages):
            # Check if the stage already exists
            if stage_name not in existing_stages:
                # Find the minimum existing order to insert new stages before it
                min_order = db.session.query(db.func.min(BuildStage.order)).filter_by(area_id=area.id).scalar() or 1
                
                # Create new stage with order before existing stages
                stage = BuildStage(
                    area_id=area.id,
                    name=stage_name,
                    description=f"Complete {stage_name} stage",
                    order=i + 1,  # Orders starting from 1
                    is_completed=False
                )
                
                db.session.add(stage)
                print(f"  - Added stage: {stage_name}")
            else:
                print(f"  - Stage already exists: {stage_name}")
        
        # Reorder all stages for this area
        all_stages = BuildStage.query.filter_by(area_id=area.id).all()
        sorted_stages = sorted(all_stages, key=lambda s: s.name)
        
        for i, stage in enumerate(sorted_stages):
            stage.order = i + 1
            print(f"  - Reordered: {stage.name} to position {i + 1}")
            
    # Commit the changes
    db.session.commit()
    print("All early stages added successfully")