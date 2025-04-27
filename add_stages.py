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

# List of build stages to add (7-21)
build_stages = [
    "7-Exterior Wrap",
    "8-Window Installation",
    "9-Exterior Doors",
    "10-Siding",
    "11-Electrical Rough-In",
    "12-Plumbing Rough-In",
    "13-HVAC Rough-In",
    "14-Insulation",
    "15-Drywall",
    "16-Interior Trim",
    "17-Interior Doors",
    "18-Interior Paint",
    "19-Flooring",
    "20-Cabinetry & Countertops",
    "21-Final Inspection",
    "Transport Checklist"
]

# Add build stages to all areas
with app.app_context():
    # Get all areas
    areas = Area.query.all()
    
    print(f"Found {len(areas)} areas in the database")
    
    for area in areas:
        print(f"Adding stages to {area.area_type}")
        
        # Get existing stages for this area
        existing_stages = [stage.name for stage in BuildStage.query.filter_by(area_id=area.id).all()]
        
        # Get the maximum existing order to append new stages after it
        max_order = db.session.query(db.func.max(BuildStage.order)).filter_by(area_id=area.id).scalar() or 0
        
        # Add each build stage
        for i, stage_name in enumerate(build_stages):
            # Check if the stage already exists
            if stage_name not in existing_stages:
                # Create new stage with order after existing stages
                stage = BuildStage(
                    area_id=area.id,
                    name=stage_name,
                    description=f"Complete {stage_name} stage",
                    order=max_order + i + 1,  # Orders starting from max_order + 1
                    is_completed=False
                )
                
                db.session.add(stage)
                print(f"  - Added stage: {stage_name}")
            else:
                print(f"  - Stage already exists: {stage_name}")
            
    # Commit the changes
    db.session.commit()
    print("All stages added successfully")