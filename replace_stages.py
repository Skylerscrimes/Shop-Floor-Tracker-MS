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

# Organized list of stages with their departments
build_stages = [
    {"name": "1-Trailer", "department": "Carpentry"},
    {"name": "2-Floor System & Sub-Floor", "department": "Carpentry"},
    {"name": "3-Walls & Rafters", "department": "Carpentry"},
    {"name": "4-Sheathing & Roof", "department": "Carpentry"},
    {"name": "5-House Wrap & Roof Prep", "department": "Carpentry"},
    {"name": "6-Doors & Windows", "department": "Carpentry"},
    {"name": "7-Trim & Siding", "department": "Carpentry"},
    {"name": "8-Rough Plumbing HVAC & Electrical", "department": "MEP"},
    {"name": "9-Insulation", "department": "Surface & Finish"},
    {"name": "10-Drywall & Tile Prep", "department": "Surface & Finish"},
    {"name": "11-Veneers, Doors & Trim", "department": "Carpentry"},
    {"name": "12-Interior/Exterior Paint", "department": "Surface & Finish"},
    {"name": "13-Tile: Shower/Floor", "department": "Surface & Finish"},
    {"name": "14-Flooring", "department": "Carpentry"},
    {"name": "15-Cabinets & Countertops", "department": "Carpentry"},
    {"name": "16-Back-Splash", "department": "Surface & Finish"},
    {"name": "17-HVAC/Electrical Finish", "department": "MEP"},
    {"name": "18-Plumbing Finish", "department": "MEP"},
    {"name": "19-Appliances", "department": "MEP"},
    {"name": "20-Testing", "department": "MEP"},
    {"name": "21-Final Finishes", "department": "Surface & Finish"},
    {"name": "22-Packout Checklist", "department": "Quality Control"},
    {"name": "Transport Checklist", "department": "Utility"}
]

# Add build stages to all areas
with app.app_context():
    # Get all areas
    areas = Area.query.all()
    
    print(f"Found {len(areas)} areas in the database")
    
    for area in areas:
        print(f"Replacing stages for {area.area_type}")
        
        # Delete existing stages for this area
        BuildStage.query.filter_by(area_id=area.id).delete()
        db.session.commit()
        
        # Add each build stage in the specified order
        for i, stage_data in enumerate(build_stages):
            stage = BuildStage(
                area_id=area.id,
                name=stage_data["name"],
                description=f"Complete {stage_data['name']} stage ({stage_data['department']})",
                order=i + 1,  # Orders starting from 1
                is_completed=False
            )
            
            db.session.add(stage)
            print(f"  - Added stage: {stage_data['name']} (Department: {stage_data['department']})")
            
        # Commit the changes
        db.session.commit()
        
        # Update the area's departments
        departments = set(stage_data["department"] for stage_data in build_stages)
        area.departments = ", ".join(departments)
        db.session.commit()
        
        print(f"  - Updated departments for {area.area_type}: {area.departments}")
            
    print("All stages replaced successfully")