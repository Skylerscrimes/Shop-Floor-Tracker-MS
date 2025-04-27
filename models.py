from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    achievement_date = db.Column(db.DateTime, default=datetime.utcnow)
    milestone_type = db.Column(db.String(50))  # e.g., 'completion', 'progress', 'quality'
    badge_icon = db.Column(db.String(50))  # FontAwesome icon name
    badge_color = db.Column(db.String(20))  # CSS color class
    is_hidden = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'achievement_date': self.achievement_date.isoformat() if self.achievement_date else None,
            'milestone_type': self.milestone_type,
            'badge_icon': self.badge_icon,
            'badge_color': self.badge_color,
            'is_hidden': self.is_hidden
        }

class ChecklistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    instructions = db.Column(db.Text)
    is_completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'instructions': self.instructions,
            'is_completed': self.is_completed,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'order': self.order
        }

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(db.Integer, db.ForeignKey('build_stage.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    
    checklist_items = db.relationship('ChecklistItem', backref='task', lazy=True, cascade="all, delete-orphan")

    def check_completion(self):
        """Update completion status based on checklist items"""
        if not self.checklist_items:
            return False
        self.is_completed = all(item.is_completed for item in self.checklist_items)
        return self.is_completed

    def to_dict(self):
        self.check_completion()  # Update completion status
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_completed': self.is_completed,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'order': self.order,
            'checklist_items': [item.to_dict() for item in self.checklist_items]
        }

class BuildStage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)  # To maintain stage order
    is_completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    
    tasks = db.relationship('Task', backref='stage', lazy=True, cascade="all, delete-orphan")
    
    # Sign-off fields
    dept_lead_signoff = db.Column(db.Boolean, default=False)
    dept_lead_signoff_date = db.Column(db.DateTime, nullable=True)
    dept_lead_name = db.Column(db.String(100), nullable=True)
    
    prod_manager_signoff = db.Column(db.Boolean, default=False)
    prod_manager_signoff_date = db.Column(db.DateTime, nullable=True)
    prod_manager_name = db.Column(db.String(100), nullable=True)
    
    # Quality control fields
    qc_flagged = db.Column(db.Boolean, default=False)
    qc_flag_reason = db.Column(db.Text, nullable=True)
    qc_flag_date = db.Column(db.DateTime, nullable=True)
    qc_officer_name = db.Column(db.String(100), nullable=True)
    
    def can_complete(self):
        """Check if all tasks are completed before allowing stage completion"""
        if not self.tasks:  # If no tasks, stage can be completed
            return True
        return all(task.is_completed for task in self.tasks)

    def check_completion(self):
        """Update completion status based on tasks"""
        if not self.tasks:
            return False
        self.is_completed = all(task.is_completed for task in self.tasks)
        return self.is_completed

    def to_dict(self):
        self.check_completion()  # Update completion status
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'order': self.order,
            'is_completed': self.is_completed,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'can_complete': self.can_complete(),
            'tasks': [task.to_dict() for task in self.tasks],
            'dept_lead_signoff': self.dept_lead_signoff,
            'dept_lead_signoff_date': self.dept_lead_signoff_date.isoformat() if self.dept_lead_signoff_date else None,
            'dept_lead_name': self.dept_lead_name,
            'prod_manager_signoff': self.prod_manager_signoff,
            'prod_manager_signoff_date': self.prod_manager_signoff_date.isoformat() if self.prod_manager_signoff_date else None,
            'prod_manager_name': self.prod_manager_name,
            'qc_flagged': self.qc_flagged,
            'qc_flag_reason': self.qc_flag_reason,
            'qc_flag_date': self.qc_flag_date.isoformat() if self.qc_flag_date else None,
            'qc_officer_name': self.qc_officer_name
        }

class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area_type = db.Column(db.String(20), nullable=False)  # 'bay1', 'bay2', 'bay3', 'bay4', 'ramp'
    name = db.Column(db.String(100))
    serial = db.Column(db.String(100))
    phase = db.Column(db.String(100))
    stages = db.Column(db.String(100))
    departments = db.Column(db.String(100))
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with build stages
    build_stages = db.relationship('BuildStage', backref='area', lazy=True, cascade="all, delete-orphan")
    # Relationship with achievements
    achievements = db.relationship('Achievement', backref='area', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'area_type': self.area_type,
            'name': self.name,
            'serial': self.serial,
            'phase': self.phase,
            'stages': self.stages,
            'departments': self.departments,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'build_stages': [stage.to_dict() for stage in self.build_stages],
            'achievements': [achievement.to_dict() for achievement in self.achievements if not achievement.is_hidden]
        }
    
    def get_progress_percentage(self):
        """Calculate the percentage of completed stages"""
        if not self.build_stages:
            return 0
        
        total_stages = len(self.build_stages)
        completed_stages = sum(1 for stage in self.build_stages if stage.is_completed)
        
        if total_stages == 0:
            return 0
            
        return int((completed_stages / total_stages) * 100)
        
    def get_current_week(self):
        """Calculate the current week number from start date"""
        if not self.start_date:
            return None
            
        today = datetime.utcnow().date()
        days_since_start = (today - self.start_date).days
        
        if days_since_start < 0:
            # Build hasn't started yet
            start_date_formatted = self.start_date.strftime('%b %d, %Y')
            return f"Scheduled to start: {start_date_formatted}"
            
        # Calculate the week number (starting from week 1)
        current_week = (days_since_start // 7) + 1
        
        # If there's an end date and we've passed it
        if self.end_date and today > self.end_date:
            return "Completed"
        
        # Show current week number and progress
        progress = self.get_progress_percentage()
        return f"Week {current_week} ({progress}% complete)"