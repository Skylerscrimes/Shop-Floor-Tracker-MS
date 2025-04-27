import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
from werkzeug.utils import secure_filename
from models import db, Area, BuildStage, Achievement, Task, ChecklistItem

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure file uploads
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Create tables and handle migrations
with app.app_context():
    # Check if we need to add new columns for existing database
    inspector = db.inspect(db.engine)
    
    # Check area table columns
    area_columns = []
    if 'area' in inspector.get_table_names():
        area_columns = [col['name'] for col in inspector.get_columns('area')]
    area_needs_migration = area_columns and ('start_date' not in area_columns or 'end_date' not in area_columns)
    
    # Check build_stage table columns
    build_stage_columns = []
    if 'build_stage' in inspector.get_table_names():
        build_stage_columns = [col['name'] for col in inspector.get_columns('build_stage')]
    build_stage_needs_migration = build_stage_columns and (
        'dept_lead_signoff' not in build_stage_columns or
        'prod_manager_signoff' not in build_stage_columns or
        'qc_flagged' not in build_stage_columns
    )
    
    # Perform area table migration if needed
    if area_needs_migration:
        app.logger.info("Migrating database: Adding start_date and end_date columns to area table")
        try:
            with db.engine.connect() as conn:
                if 'start_date' not in area_columns:
                    conn.execute(db.text("ALTER TABLE area ADD COLUMN start_date DATE"))
                if 'end_date' not in area_columns:
                    conn.execute(db.text("ALTER TABLE area ADD COLUMN end_date DATE"))
                conn.commit()
        except Exception as e:
            app.logger.error(f"Area table migration error: {e}")
    
    # Now create all tables
    db.create_all()
    
    # Perform build_stage table migration if needed
    if build_stage_needs_migration:
        app.logger.info("Migrating database: Adding sign-off columns to build_stage table")
        try:
            with db.engine.connect() as conn:
                # Department Lead fields
                if 'dept_lead_signoff' not in build_stage_columns:
                    conn.execute(db.text("ALTER TABLE build_stage ADD COLUMN dept_lead_signoff BOOLEAN DEFAULT FALSE"))
                if 'dept_lead_signoff_date' not in build_stage_columns:
                    conn.execute(db.text("ALTER TABLE build_stage ADD COLUMN dept_lead_signoff_date TIMESTAMP"))
                if 'dept_lead_name' not in build_stage_columns:
                    conn.execute(db.text("ALTER TABLE build_stage ADD COLUMN dept_lead_name VARCHAR(100)"))
                
                # Production Manager fields
                if 'prod_manager_signoff' not in build_stage_columns:
                    conn.execute(db.text("ALTER TABLE build_stage ADD COLUMN prod_manager_signoff BOOLEAN DEFAULT FALSE"))
                if 'prod_manager_signoff_date' not in build_stage_columns:
                    conn.execute(db.text("ALTER TABLE build_stage ADD COLUMN prod_manager_signoff_date TIMESTAMP"))
                if 'prod_manager_name' not in build_stage_columns:
                    conn.execute(db.text("ALTER TABLE build_stage ADD COLUMN prod_manager_name VARCHAR(100)"))
                
                # Quality Control fields
                if 'qc_flagged' not in build_stage_columns:
                    conn.execute(db.text("ALTER TABLE build_stage ADD COLUMN qc_flagged BOOLEAN DEFAULT FALSE"))
                if 'qc_flag_reason' not in build_stage_columns:
                    conn.execute(db.text("ALTER TABLE build_stage ADD COLUMN qc_flag_reason TEXT"))
                if 'qc_flag_date' not in build_stage_columns:
                    conn.execute(db.text("ALTER TABLE build_stage ADD COLUMN qc_flag_date TIMESTAMP"))
                if 'qc_officer_name' not in build_stage_columns:
                    conn.execute(db.text("ALTER TABLE build_stage ADD COLUMN qc_officer_name VARCHAR(100)"))
                
                conn.commit()
        except Exception as e:
            app.logger.error(f"Build stage table migration error: {e}")
    
    # Initialize empty areas if they don't exist
    for area_type in ['bay1', 'bay2', 'bay3', 'bay4', 'ramp']:
        if not Area.query.filter_by(area_type=area_type).first():
            db.session.add(Area(area_type=area_type))
    db.session.commit()

@app.route('/')
def index():
    return redirect(url_for('qc_officer_default'))

@app.route('/qc-officer')
@app.route('/qc-officer/<department>')
def qc_officer(department="All"):
    return render_template('qc_officer.html', department=department)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # First check if already authenticated
    admin_auth = request.cookies.get('admin_auth')
    if admin_auth == '0143':
        return render_template('admin.html', show_login=False)

    # Handle login attempt
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '0143':
            response = make_response(redirect(url_for('admin')))
            response.set_cookie('admin_auth', '0143', secure=True, httponly=True)
            return response
        return render_template('admin.html', show_login=True, error="Incorrect password")

    # Not authenticated, show login page
    return render_template('admin.html', show_login=True)

@app.route('/dept-admin')
@app.route('/dept-admin/')
def dept_admin_default():
    return render_template('dept_admin.html', department="Carpentry")

@app.route('/mep-admin')
def mep_admin():
    return render_template('mep_admin.html', department="MEP")

@app.route('/surface-finish-admin')
def surface_finish_admin():
    return render_template('surface_finish_admin.html', department="Surface & Finish")

@app.route('/utility-admin')
def utility_admin():
    return render_template('utility_admin.html', department="Utility")

@app.route('/prod-manager')
@app.route('/prod-manager/')
def prod_manager_default():
    return render_template('prod_manager.html', department="All")

@app.route('/qc-officer')
@app.route('/qc-officer/')
def qc_officer_default():
    return render_template('qc_officer.html', department="All")

@app.route('/api/department-stages/<department>')
def get_department_stages(department):
    """Get all stages for a specific department across all areas"""
    areas = Area.query.all()
    stages_by_area = {}
    
    for area in areas:
        if department.lower() == "all":
            # Get all stages for all departments
            dept_stages = [stage.to_dict() for stage in area.build_stages]
        else:
            # Filter stages for specific department
            dept_stages = [
                stage.to_dict() for stage in area.build_stages 
                if stage.description and department in stage.description
            ]
        
        if dept_stages:
            stages_by_area[area.area_type] = dept_stages
    
    return jsonify(stages_by_area)

@app.route('/display')
def display():
    return render_template('display.html')

@app.route('/api/areas', methods=['GET'])
def get_areas():
    areas = Area.query.all()
    areas_dict = {}
    
    for area in areas:
        # Get build stages for progress calculation
        ordered_stages = sorted(area.build_stages, key=lambda stage: stage.order)
        build_stages = [stage.to_dict() for stage in ordered_stages]
        total_stages = len(build_stages)
        completed_stages = sum(1 for stage in build_stages if stage['is_completed'])
        
        # Calculate progress percentage
        progress_percentage = area.get_progress_percentage()
        
        # Find the next task's department
        next_department = None
        next_stage = None
        for stage in ordered_stages:
            if not stage.is_completed:
                stage_description = stage.description if stage.description else ""
                # Extract department from stage description which is in the format: "... (Department)"
                if "(" in stage_description and ")" in stage_description:
                    dept_start = stage_description.rfind("(") + 1
                    dept_end = stage_description.rfind(")")
                    if dept_start < dept_end:
                        next_department = stage_description[dept_start:dept_end].strip()
                        next_stage = stage.name
                break
        
        # Exclude Production Manager, Quality Control from departments display
        displayed_departments = next_department
        if not displayed_departments or displayed_departments in ["Quality Control", "Production Manager"]:
            displayed_departments = ""
        
        areas_dict[area.area_type] = {
            'name': area.name,
            'serial': area.serial,
            'phase': area.phase,
            'stages': area.stages,
            'departments': displayed_departments,  # Only show the next task's department
            'next_stage': next_stage,
            'start_date': area.start_date.isoformat() if area.start_date else None,
            'end_date': area.end_date.isoformat() if area.end_date else None,
            'week_status': area.get_current_week(),
            'progress': progress_percentage,
            'build_stages': build_stages,
            'completed_stages': completed_stages,
            'total_stages': total_stages
        }
        
    data = {
        'lastUpdated': datetime.utcnow().isoformat(),
        **areas_dict
    }
    
    return jsonify(data)

@app.route('/api/areas', methods=['POST'])
def update_areas():
    data = request.json
    
    try:
        # Update each area in the database
        for area_type in ['bay1', 'bay2', 'bay3', 'bay4', 'ramp']:
            if area_type in data:
                area = Area.query.filter_by(area_type=area_type).first()
                
                if not area:
                    area = Area(area_type=area_type)
                    db.session.add(area)
                
                area_data = data[area_type]
                area.name = area_data.get('name', '')
                area.serial = area_data.get('serial', '')
                area.phase = area_data.get('phase', '')
                area.stages = area_data.get('stages', '')
                area.departments = area_data.get('departments', '')
                
                # Handle start and end dates
                if 'start_date' in area_data and area_data['start_date']:
                    area.start_date = datetime.fromisoformat(area_data['start_date']).date()
                else:
                    area.start_date = None
                    
                if 'end_date' in area_data and area_data['end_date']:
                    area.end_date = datetime.fromisoformat(area_data['end_date']).date()
                else:
                    area.end_date = None
                    
                area.last_updated = datetime.utcnow()
        
        db.session.commit()
        return jsonify({"success": True, "message": "Data saved successfully"})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving data: {str(e)}")
        return jsonify({"success": False, "message": f"Error saving data: {str(e)}"}), 500

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-logo', methods=['POST'])
def upload_logo():
    # Check if a file was submitted
    if 'logo' not in request.files:
        return jsonify({"success": False, "message": "No file provided"}), 400
    
    file = request.files['logo']
    
    # Check if the file is empty
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
    
    # Check if the file is allowed
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Save as company_logo with original extension
        extension = filename.rsplit('.', 1)[1].lower()
        save_filename = f"company_logo.{extension}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], save_filename))
        return jsonify({
            "success": True, 
            "message": "Logo uploaded successfully",
            "logoPath": f"/static/images/{save_filename}"
        })
    
    return jsonify({"success": False, "message": "File type not allowed"}), 400

@app.route('/api/logo', methods=['GET'])
def get_logo():
    # Find any file that starts with company_logo in the images directory
    logo_path = None
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.startswith('company_logo.'):
            logo_path = f"/static/images/{filename}"
            break
    
    return jsonify({"success": True, "logoPath": logo_path})

@app.route('/api/tasks/<int:stage_id>', methods=['GET', 'POST'])
def manage_tasks(stage_id):
    stage = BuildStage.query.get_or_404(stage_id)
    if request.method == 'POST':
        data = request.json
        
        # Find all stages with the same name
        matching_stages = BuildStage.query.filter_by(name=stage.name).all()
        
        created_tasks = []
        for matching_stage in matching_stages:
            task = Task(
                stage_id=matching_stage.id,
                name=data['name'],
                description=data.get('description', ''),
                order=data.get('order', 0)
            )
            db.session.add(task)
            created_tasks.append(task)
            
        db.session.commit()
        return jsonify(created_tasks[0].to_dict())
    return jsonify([task.to_dict() for task in stage.tasks])

@app.route('/api/checklist-items/<int:task_id>', methods=['GET', 'POST'])
def manage_checklist_items(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        data = request.json
        item = ChecklistItem(
            task_id=task_id,
            name=data['name'],
            instructions=data.get('instructions', ''),
            order=data.get('order', 0)
        )
        db.session.add(item)
        db.session.commit()
        return jsonify(item.to_dict())
    return jsonify([item.to_dict() for item in task.checklist_items])

@app.route('/checklist/<area_type>', methods=['GET'])
def checklist(area_type):
    """Render the checklist page for a specific area with role-based access"""
    area = Area.query.filter_by(area_type=area_type).first_or_404()
    
    # Get the referrer to determine the user's role
    referrer = request.referrer or ''
    user_role = None
    
    # Extract role from referrer URL
    if '/mep-admin' in referrer:
        user_role = 'mep-admin'
    elif '/surface-finish-admin' in referrer:
        user_role = 'surface-finish-admin'
    elif '/utility-admin' in referrer:
        user_role = 'utility-admin'
    elif '/dept-admin' in referrer:
        user_role = 'dept-admin'
    elif '/qc-officer' in referrer:
        user_role = 'qc-officer'
    elif '/prod-manager' in referrer:
        user_role = 'prod-manager'
    elif '/admin' in referrer:
        user_role = 'admin'
    
    # Allow access for admin, QC officers, and production managers
    if user_role in ['admin', 'qc-officer', 'prod-manager']:
        return render_template('checklist.html', area=area, user_role=user_role)
    
    # Check department-specific permissions
    if user_role == 'mep-admin' and 'MEP' in (area.departments or ''):
        return render_template('checklist.html', area=area, user_role=user_role)
    elif user_role == 'surface-finish-admin' and 'Surface & Finish' in (area.departments or ''):
        return render_template('checklist.html', area=area, user_role=user_role)
    elif user_role == 'utility-admin' and 'Utility' in (area.departments or ''):
        return render_template('checklist.html', area=area, user_role=user_role)
    elif user_role == 'dept-admin' and 'Carpentry' in (area.departments or ''):
        return render_template('checklist.html', area=area, user_role=user_role)
    
    return "Access denied. Please ensure you have the correct role and permissions.", 403
        
    return render_template('checklist.html', area=area, user_role=user_role)

@app.route('/api/stages/<area_type>', methods=['GET'])
def get_stages(area_type):
    """Get all stages for a specific area"""
    area = Area.query.filter_by(area_type=area_type).first_or_404()
    
    # Return stages with their completion status
    return jsonify({
        "success": True,
        "area": area.to_dict(),
        "stages": [stage.to_dict() for stage in area.build_stages]
    })

@app.route('/api/stages/<area_type>', methods=['POST'])
def add_stage(area_type):
    """Add a new stage to an area with role-based access"""
    area = Area.query.filter_by(area_type=area_type).first_or_404()
    
    # Get the user's role from the referrer
    user_role = request.referrer.split('/')[3] if request.referrer else None
    
    # Only allow admins and managers to add stages
    if user_role not in ['admin', 'prod-manager', 'mep-admin', 'surface-finish-admin', 'utility-admin', 'dept-admin']:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    data = request.json
    
    try:
        # Get the highest order value and add 1 for new stage
        max_order = db.session.query(db.func.max(BuildStage.order)).filter_by(area_id=area.id).scalar() or 0
        
        # Create new stage
        new_stage = BuildStage(
            area_id=area.id,
            name=data.get('name', 'New Stage'),
            description=data.get('description', ''),
            order=max_order + 1,
            is_completed=False
        )
        
        db.session.add(new_stage)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Stage added successfully",
            "stage": new_stage.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding stage: {str(e)}")
        return jsonify({"success": False, "message": f"Error adding stage: {str(e)}"}), 500

@app.route('/api/stages/<int:stage_id>', methods=['PUT'])
def update_stage(stage_id):
    """Update a specific stage and sync changes to matching stages"""
    stage = BuildStage.query.get_or_404(stage_id)
    data = request.json
    area = stage.area  # Get the associated area for achievements
    
    try:
        state_changed = False  # Flag to track if completion or sign-off status changed
        original_name = stage.name
        
        # Find all stages with the same name across all areas
        matching_stages = BuildStage.query.filter_by(name=original_name).all()
        
        # Update all matching stages
        for matching_stage in matching_stages:
            if 'name' in data:
                matching_stage.name = data['name']
            if 'description' in data:
                matching_stage.description = data['description']
            if 'order' in data:
                matching_stage.order = data['order']
        if 'is_completed' in data:
            was_completed = stage.is_completed
            stage.is_completed = data['is_completed']
            
            # If stage is now completed and wasn't before, set completion date
            if stage.is_completed and not was_completed:
                stage.completion_date = datetime.utcnow()
                state_changed = True
            # If stage is now not completed but was before, clear completion date
            elif not stage.is_completed and was_completed:
                stage.completion_date = None
                state_changed = True
        
        # Department Lead Sign-off fields
        if 'dept_lead_signoff' in data:
            was_signed = stage.dept_lead_signoff
            stage.dept_lead_signoff = data['dept_lead_signoff']
            
            # If newly signed, set date
            if stage.dept_lead_signoff and not was_signed:
                stage.dept_lead_signoff_date = datetime.utcnow()
                state_changed = True
            # If now unsigned, clear date
            elif not stage.dept_lead_signoff and was_signed:
                stage.dept_lead_signoff_date = None
                state_changed = True
                
        if 'dept_lead_name' in data:
            stage.dept_lead_name = data['dept_lead_name']
            
        # Production Manager Sign-off fields
        if 'prod_manager_signoff' in data:
            was_signed = stage.prod_manager_signoff
            stage.prod_manager_signoff = data['prod_manager_signoff']
            
            # If newly signed, set date
            if stage.prod_manager_signoff and not was_signed:
                stage.prod_manager_signoff_date = datetime.utcnow()
                state_changed = True
            # If now unsigned, clear date
            elif not stage.prod_manager_signoff and was_signed:
                stage.prod_manager_signoff_date = None
                state_changed = True
                
        if 'prod_manager_name' in data:
            stage.prod_manager_name = data['prod_manager_name']
            
        # Quality Control fields
        if 'qc_flagged' in data:
            was_flagged = stage.qc_flagged
            stage.qc_flagged = data['qc_flagged']
            
            # If newly flagged, set date
            if stage.qc_flagged and not was_flagged:
                stage.qc_flag_date = datetime.utcnow()
                state_changed = True
            # If now unflagged, clear date
            elif not stage.qc_flagged and was_flagged:
                stage.qc_flag_date = None
                state_changed = True
                
        if 'qc_flag_reason' in data:
            stage.qc_flag_reason = data['qc_flag_reason']
            
        if 'qc_officer_name' in data:
            stage.qc_officer_name = data['qc_officer_name']
        
        db.session.commit()
        
        # Check if we need to generate achievements
        if state_changed:
            generate_achievements(stage, area)
        
        return jsonify({
            "success": True,
            "message": "Stage updated successfully",
            "stage": stage.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating stage: {str(e)}")
        return jsonify({"success": False, "message": f"Error updating stage: {str(e)}"}), 500

@app.route('/api/stages/<int:stage_id>', methods=['DELETE'])
def delete_stage(stage_id):
    """Delete a specific stage"""
    stage = BuildStage.query.get_or_404(stage_id)
    
    try:
        db.session.delete(stage)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Stage deleted successfully"
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting stage: {str(e)}")
        return jsonify({"success": False, "message": f"Error deleting stage: {str(e)}"}), 500

@app.route('/api/stages/reorder', methods=['POST'])
def reorder_stages():
    """Reorder stages"""
    data = request.json
    stages_order = data.get('stages', [])
    
    try:
        for stage_data in stages_order:
            stage_id = stage_data.get('id')
            new_order = stage_data.get('order')
            
            if stage_id and new_order is not None:
                stage = BuildStage.query.get(stage_id)
                if stage:
                    stage.order = new_order
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Stages reordered successfully"
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error reordering stages: {str(e)}")
        return jsonify({"success": False, "message": f"Error reordering stages: {str(e)}"}), 500

# Achievement system API endpoints
@app.route('/api/achievements/<area_type>', methods=['GET'])
def get_achievements(area_type):
    """Get all achievements for a specific area"""
    area = Area.query.filter_by(area_type=area_type).first_or_404()
    
    # Return only non-hidden achievements
    achievements = [a.to_dict() for a in area.achievements if not a.is_hidden]
    
    return jsonify({
        "success": True,
        "area": area.area_type,
        "achievements": achievements
    })

@app.route('/api/achievements/<area_type>', methods=['POST'])
def add_achievement(area_type):
    """Add a new achievement to an area"""
    area = Area.query.filter_by(area_type=area_type).first_or_404()
    data = request.json
    
    try:
        # Create new achievement
        new_achievement = Achievement(
            area_id=area.id,
            title=data.get('title', 'New Achievement'),
            description=data.get('description', ''),
            milestone_type=data.get('milestone_type', 'progress'),
            badge_icon=data.get('badge_icon', 'trophy'),
            badge_color=data.get('badge_color', 'warning'),
            is_hidden=data.get('is_hidden', False)
        )
        
        db.session.add(new_achievement)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Achievement added successfully",
            "achievement": new_achievement.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding achievement: {str(e)}")
        return jsonify({"success": False, "message": f"Error adding achievement: {str(e)}"}), 500

@app.route('/api/achievements/<int:achievement_id>', methods=['PUT'])
def update_achievement(achievement_id):
    """Update a specific achievement"""
    achievement = Achievement.query.get_or_404(achievement_id)
    data = request.json
    
    try:
        if 'title' in data:
            achievement.title = data['title']
        if 'description' in data:
            achievement.description = data['description']
        if 'milestone_type' in data:
            achievement.milestone_type = data['milestone_type']
        if 'badge_icon' in data:
            achievement.badge_icon = data['badge_icon']
        if 'badge_color' in data:
            achievement.badge_color = data['badge_color']
        if 'is_hidden' in data:
            achievement.is_hidden = data['is_hidden']
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Achievement updated successfully",
            "achievement": achievement.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating achievement: {str(e)}")
        return jsonify({"success": False, "message": f"Error updating achievement: {str(e)}"}), 500

@app.route('/api/achievements/<int:achievement_id>', methods=['DELETE'])
def delete_achievement(achievement_id):
    """Delete a specific achievement"""
    achievement = Achievement.query.get_or_404(achievement_id)
    
    try:
        db.session.delete(achievement)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Achievement deleted successfully"
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting achievement: {str(e)}")
        return jsonify({"success": False, "message": f"Error deleting achievement: {str(e)}"}), 500

# Auto-generate achievements when stages are completed
def generate_achievements(stage, area):
    """Generate achievements based on stage completion"""
    try:
        # Check for a 25% milestone
        progress = area.get_progress_percentage()
        total_stages = len(area.build_stages)
        completed_stages = sum(1 for s in area.build_stages if s.is_completed)
        
        # Only generate progress achievements for key milestones (25%, 50%, 75%, 100%)
        for milestone in [25, 50, 75, 100]:
            # Check if we've reached or crossed this milestone for the first time
            if progress >= milestone and progress - (100 / total_stages) < milestone:
                # Check if we already have this achievement
                existing = Achievement.query.filter_by(
                    area_id=area.id,
                    milestone_type=f"progress-{milestone}"
                ).first()
                
                if not existing:
                    # Create a new achievement for this milestone
                    achievement = Achievement(
                        area_id=area.id,
                        title=f"{milestone}% Complete Milestone",
                        description=f"Congratulations! {area.name or area.area_type.capitalize()} has reached {milestone}% completion with {completed_stages} completed stages.",
                        milestone_type=f"progress-{milestone}",
                        badge_icon="award",
                        badge_color="success" if milestone == 100 else "warning",
                        is_hidden=False
                    )
                    db.session.add(achievement)
                    db.session.commit()
                    app.logger.info(f"Created {milestone}% progress achievement for {area.area_type}")
                    
        # Check for a quality achievement (all sign-offs complete on a stage)
        if (stage.is_completed and stage.dept_lead_signoff and 
            stage.prod_manager_signoff and not stage.qc_flagged):
            # This is a fully verified high-quality stage completion
            # Check if we already have a quality achievement for this stage
            existing = Achievement.query.filter_by(
                area_id=area.id,
                milestone_type=f"quality-stage-{stage.id}"
            ).first()
            
            if not existing:
                # Create a new achievement for quality completion
                achievement = Achievement(
                    area_id=area.id,
                    title=f"Quality Excellence: {stage.name}",
                    description=f"The '{stage.name}' stage was completed with all quality checks and sign-offs.",
                    milestone_type=f"quality-stage-{stage.id}",
                    badge_icon="star",
                    badge_color="info",
                    is_hidden=False
                )
                db.session.add(achievement)
                db.session.commit()
                app.logger.info(f"Created quality achievement for {stage.name} in {area.area_type}")
                
    except Exception as e:
        app.logger.error(f"Error generating achievements: {str(e)}")
        # Don't let achievement generation failure stop the main operation
        db.session.rollback()

# Update the stage update route to potentially generate achievements
@app.route('/achievements/<area_type>', methods=['GET'])
def achievements_page(area_type):
    """Render the achievements page for a specific area"""
    area = Area.query.filter_by(area_type=area_type).first_or_404()
    return render_template('achievements.html', area=area)

@app.route('/policies')
def policies():
    return render_template('policies.html')

@app.route('/api/policies/upload', methods=['POST'])
def upload_policy():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
        
    # Save file logic here
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'policies', filename))
    
    # Save metadata to database
    # Implementation depends on your database schema

    return jsonify({"success": True, "message": "File uploaded successfully"})

@app.route('/api/policies', methods=['GET'])
def get_policies():
    # Implement fetching policies from database
    return jsonify({"success": True, "policies": []})

@app.route('/api/policies/<int:policy_id>', methods=['DELETE'])
def delete_policy(policy_id):
    # Implement policy deletion
    return jsonify({"success": True, "message": "Policy deleted successfully"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
