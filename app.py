"""
QA Testing Checklist Application
Flask Backend with Local JSON Storage
Python Version: 3.12.8
Flask Version: 3.1.2
"""

from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
from pathlib import Path
import traceback

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# File paths
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

CURRENT_SESSION_FILE = DATA_DIR / 'current_session.json'
COMPLETED_FILE = DATA_DIR / 'completed.json'
DEFAULT_CHECKLIST_FILE = Path('default_checklist.json')

# Load default checklist from external JSON file
def load_default_checklist():
    """Load default checklist from external JSON file"""
    try:
        if DEFAULT_CHECKLIST_FILE.exists():
            with open(DEFAULT_CHECKLIST_FILE, 'r', encoding='utf-8') as f:
                checklist = json.load(f)
                print(f"✓ Loaded default checklist from {DEFAULT_CHECKLIST_FILE}")
                return checklist
        else:
            print(f"✗ Default checklist file not found: {DEFAULT_CHECKLIST_FILE}")
            print("  Please create 'default_checklist.json' in the project root directory")
            return []
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing default_checklist.json: {str(e)}")
        return []
    except Exception as e:
        print(f"✗ Error loading default checklist: {str(e)}")
        traceback.print_exc()
        return []

# Load default checklist at startup
DEFAULT_CHECKLIST = load_default_checklist()

# Initialize data files if they don't exist
def init_data_files():
    """Initialize JSON data files with default structure"""
    try:
        # Check and fix current_session.json
        needs_init = False
        if not CURRENT_SESSION_FILE.exists():
            needs_init = True
        else:
            # Check if file is valid
            try:
                with open(CURRENT_SESSION_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content or content == '':
                        needs_init = True
                    else:
                        json.loads(content)  # Try to parse
            except (json.JSONDecodeError, Exception):
                needs_init = True
        
        if needs_init:
            default_session = {
                "target_website": "",
                "start_date": "",
                "checklist": DEFAULT_CHECKLIST,
                "notes": []
            }
            save_json(CURRENT_SESSION_FILE, default_session)
            print(f"✓ Created/Fixed {CURRENT_SESSION_FILE}")
        
        # Check and fix completed.json
        needs_init_completed = False
        if not COMPLETED_FILE.exists():
            needs_init_completed = True
        else:
            try:
                with open(COMPLETED_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content or content == '':
                        needs_init_completed = True
                    else:
                        json.loads(content)  # Try to parse
            except (json.JSONDecodeError, Exception):
                needs_init_completed = True
        
        if needs_init_completed:
            save_json(COMPLETED_FILE, [])
            print(f"✓ Created/Fixed {COMPLETED_FILE}")
            
    except Exception as e:
        print(f"✗ Error initializing data files: {str(e)}")
        traceback.print_exc()

def load_json(filepath):
    """Load JSON data from file"""
    try:
        if not filepath.exists():
            print(f"File not found: {filepath}")
            return None
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
            # Check if file is empty
            if not content or content == '':
                print(f"File is empty: {filepath}")
                return None
            
            return json.loads(content)
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error in {filepath}: {str(e)}")
        print(f"File content length: {len(content) if 'content' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"Error loading {filepath}: {str(e)}")
        traceback.print_exc()
        return None

def save_json(filepath, data):
    """Save JSON data to file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {str(e)}")
        traceback.print_exc()
        return False

# Routes
@app.route('/')
def index():
    """Main checklist page"""
    return render_template('index.html')

@app.route('/history')
def history():
    """Completed projects history page"""
    return render_template('history.html')

# API Endpoints
@app.route('/api/session', methods=['GET'])
def get_session():
    """Get current session data"""
    try:
        session_data = load_json(CURRENT_SESSION_FILE)
        
        # If file is corrupted or empty, reinitialize
        if session_data is None:
            print("Session data is None, reinitializing...")
            init_data_files()
            session_data = load_json(CURRENT_SESSION_FILE)
        
        # If still None, create default session manually
        if session_data is None:
            print("Creating default session manually...")
            session_data = {
                "target_website": "",
                "start_date": "",
                "checklist": DEFAULT_CHECKLIST if DEFAULT_CHECKLIST else [],
                "notes": []
            }
            save_json(CURRENT_SESSION_FILE, session_data)
        
        return jsonify(session_data), 200
        
    except Exception as e:
        print(f"Error in get_session: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/session/info', methods=['POST'])
def update_session_info():
    """Update target website and start date"""
    try:
        data = request.get_json()
        session_data = load_json(CURRENT_SESSION_FILE)
        
        if session_data is None:
            return jsonify({"error": "Session data not found"}), 500
        
        if 'target_website' in data:
            session_data['target_website'] = data['target_website']
        if 'start_date' in data:
            session_data['start_date'] = data['start_date']
        
        if save_json(CURRENT_SESSION_FILE, session_data):
            return jsonify({"success": True, "data": session_data}), 200
        return jsonify({"error": "Failed to save session"}), 500
    except Exception as e:
        print(f"Error in update_session_info: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/checklist/item', methods=['POST'])
def toggle_checklist_item():
    """Toggle checklist item checked status"""
    try:
        data = request.get_json()
        heading_id = data.get('heading_id')
        item_id = data.get('item_id')
        checked = data.get('checked')
        
        session_data = load_json(CURRENT_SESSION_FILE)
        
        if session_data is None:
            return jsonify({"error": "Session data not found"}), 500
        
        for heading in session_data['checklist']:
            if heading['id'] == heading_id:
                for item in heading['items']:
                    if item['id'] == item_id:
                        item['checked'] = checked
                        break
                break
        
        if save_json(CURRENT_SESSION_FILE, session_data):
            return jsonify({"success": True}), 200
        return jsonify({"error": "Failed to save"}), 500
    except Exception as e:
        print(f"Error in toggle_checklist_item: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/checklist/heading', methods=['POST'])
def add_heading():
    """Add new heading to checklist"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        
        if not title:
            return jsonify({"error": "Title is required"}), 400
        
        session_data = load_json(CURRENT_SESSION_FILE)
        
        if session_data is None:
            return jsonify({"error": "Session data not found"}), 500
        
        # Get max ID
        max_id = max([h['id'] for h in session_data['checklist']], default=0)
        
        new_heading = {
            "id": max_id + 1,
            "title": title,
            "items": []
        }
        
        session_data['checklist'].append(new_heading)
        
        if save_json(CURRENT_SESSION_FILE, session_data):
            return jsonify({"success": True, "heading": new_heading}), 200
        return jsonify({"error": "Failed to save"}), 500
    except Exception as e:
        print(f"Error in add_heading: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/checklist/heading/<int:heading_id>', methods=['PUT'])
def edit_heading(heading_id):
    """Edit heading title"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        
        if not title:
            return jsonify({"error": "Title is required"}), 400
        
        session_data = load_json(CURRENT_SESSION_FILE)
        
        if session_data is None:
            return jsonify({"error": "Session data not found"}), 500
        
        for heading in session_data['checklist']:
            if heading['id'] == heading_id:
                heading['title'] = title
                break
        
        if save_json(CURRENT_SESSION_FILE, session_data):
            return jsonify({"success": True}), 200
        return jsonify({"error": "Failed to save"}), 500
    except Exception as e:
        print(f"Error in edit_heading: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/checklist/heading/<int:heading_id>', methods=['DELETE'])
def delete_heading(heading_id):
    """Delete heading from checklist"""
    try:
        session_data = load_json(CURRENT_SESSION_FILE)
        
        if session_data is None:
            return jsonify({"error": "Session data not found"}), 500
        
        session_data['checklist'] = [h for h in session_data['checklist'] if h['id'] != heading_id]
        
        if save_json(CURRENT_SESSION_FILE, session_data):
            return jsonify({"success": True}), 200
        return jsonify({"error": "Failed to save"}), 500
    except Exception as e:
        print(f"Error in delete_heading: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/checklist/item', methods=['PUT'])
def add_item():
    """Add new item to heading"""
    try:
        data = request.get_json()
        heading_id = data.get('heading_id')
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        session_data = load_json(CURRENT_SESSION_FILE)
        
        if session_data is None:
            return jsonify({"error": "Session data not found"}), 500
        
        for heading in session_data['checklist']:
            if heading['id'] == heading_id:
                # Get max item ID
                max_id = max([item['id'] for item in heading['items']], default=0)
                
                new_item = {
                    "id": max_id + 1,
                    "text": text,
                    "checked": False
                }
                
                heading['items'].append(new_item)
                break
        
        if save_json(CURRENT_SESSION_FILE, session_data):
            return jsonify({"success": True, "item": new_item}), 200
        return jsonify({"error": "Failed to save"}), 500
    except Exception as e:
        print(f"Error in add_item: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/checklist/item/<int:heading_id>/<int:item_id>', methods=['PUT'])
def edit_item(heading_id, item_id):
    """Edit item text"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        session_data = load_json(CURRENT_SESSION_FILE)
        
        if session_data is None:
            return jsonify({"error": "Session data not found"}), 500
        
        for heading in session_data['checklist']:
            if heading['id'] == heading_id:
                for item in heading['items']:
                    if item['id'] == item_id:
                        item['text'] = text
                        break
                break
        
        if save_json(CURRENT_SESSION_FILE, session_data):
            return jsonify({"success": True}), 200
        return jsonify({"error": "Failed to save"}), 500
    except Exception as e:
        print(f"Error in edit_item: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/checklist/item/<int:heading_id>/<int:item_id>', methods=['DELETE'])
def delete_item(heading_id, item_id):
    """Delete item from heading"""
    try:
        session_data = load_json(CURRENT_SESSION_FILE)
        
        if session_data is None:
            return jsonify({"error": "Session data not found"}), 500
        
        for heading in session_data['checklist']:
            if heading['id'] == heading_id:
                heading['items'] = [item for item in heading['items'] if item['id'] != item_id]
                break
        
        if save_json(CURRENT_SESSION_FILE, session_data):
            return jsonify({"success": True}), 200
        return jsonify({"error": "Failed to save"}), 500
    except Exception as e:
        print(f"Error in delete_item: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/notes', methods=['POST'])
def add_note():
    """Add new note"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        session_data = load_json(CURRENT_SESSION_FILE)
        
        if session_data is None:
            return jsonify({"error": "Session data not found"}), 500
        
        # Get max note ID
        max_id = max([note['id'] for note in session_data['notes']], default=0)
        
        new_note = {
            "id": max_id + 1,
            "text": text,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        session_data['notes'].append(new_note)
        
        if save_json(CURRENT_SESSION_FILE, session_data):
            return jsonify({"success": True, "note": new_note}), 200
        return jsonify({"error": "Failed to save"}), 500
    except Exception as e:
        print(f"Error in add_note: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def edit_note(note_id):
    """Edit note text"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        session_data = load_json(CURRENT_SESSION_FILE)
        
        if session_data is None:
            return jsonify({"error": "Session data not found"}), 500
        
        for note in session_data['notes']:
            if note['id'] == note_id:
                note['text'] = text
                break
        
        if save_json(CURRENT_SESSION_FILE, session_data):
            return jsonify({"success": True}), 200
        return jsonify({"error": "Failed to save"}), 500
    except Exception as e:
        print(f"Error in edit_note: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete note"""
    try:
        session_data = load_json(CURRENT_SESSION_FILE)
        
        if session_data is None:
            return jsonify({"error": "Session data not found"}), 500
        
        session_data['notes'] = [note for note in session_data['notes'] if note['id'] != note_id]
        
        if save_json(CURRENT_SESSION_FILE, session_data):
            return jsonify({"success": True}), 200
        return jsonify({"error": "Failed to save"}), 500
    except Exception as e:
        print(f"Error in delete_note: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/session/complete', methods=['POST'])
def complete_session():
    """Complete current session and save to history"""
    try:
        data = request.get_json()
        end_date = data.get('end_date', datetime.now().strftime("%Y-%m-%d"))
        
        session_data = load_json(CURRENT_SESSION_FILE)
        completed_data = load_json(COMPLETED_FILE)
        
        if session_data is None or completed_data is None:
            return jsonify({"error": "Failed to load data"}), 500
        
        if not session_data['target_website']:
            return jsonify({"error": "Target website is required"}), 400
        
        # Create completed entry
        completed_entry = {
            "id": len(completed_data) + 1,
            "target_website": session_data['target_website'],
            "start_date": session_data['start_date'],
            "end_date": end_date,
            "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "checklist": session_data['checklist'],
            "notes": session_data['notes']
        }
        
        completed_data.append(completed_entry)
        
        # Reset current session with fresh checklist from default file
        reset_session = {
            "target_website": "",
            "start_date": "",
            "checklist": load_default_checklist(),  # Reload from file
            "notes": []
        }
        
        if save_json(COMPLETED_FILE, completed_data) and save_json(CURRENT_SESSION_FILE, reset_session):
            return jsonify({"success": True, "message": "Session completed successfully"}), 200
        return jsonify({"error": "Failed to save"}), 500
    except Exception as e:
        print(f"Error in complete_session: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/session/reset', methods=['POST'])
def reset_session():
    """Reset current session without saving to history"""
    try:
        # Reload checklist from default file
        reset_data = {
            "target_website": "",
            "start_date": "",
            "checklist": load_default_checklist(),  # Reload from file
            "notes": []
        }
        
        if save_json(CURRENT_SESSION_FILE, reset_data):
            return jsonify({"success": True, "message": "Session reset successfully"}), 200
        return jsonify({"error": "Failed to reset"}), 500
    except Exception as e:
        print(f"Error in reset_session: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get completed projects history"""
    try:
        completed_data = load_json(COMPLETED_FILE)
        if completed_data is not None:
            return jsonify(completed_data), 200
        return jsonify({"error": "Failed to load history"}), 500
    except Exception as e:
        print(f"Error in get_history: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/history/<int:project_id>', methods=['DELETE'])
def delete_history_entry(project_id):
    """Delete a history entry"""
    try:
        completed_data = load_json(COMPLETED_FILE)
        
        if completed_data is None:
            return jsonify({"error": "Failed to load history"}), 500
        
        completed_data = [entry for entry in completed_data if entry['id'] != project_id]
        
        if save_json(COMPLETED_FILE, completed_data):
            return jsonify({"success": True}), 200
        return jsonify({"error": "Failed to delete"}), 500
    except Exception as e:
        print(f"Error in delete_history_entry: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Check if default checklist file exists
    if not DEFAULT_CHECKLIST_FILE.exists():
        print("=" * 60)
        print("⚠️  WARNING: default_checklist.json not found!")
        print("=" * 60)
        print("Please create 'default_checklist.json' in the project root.")
        print("The application will start but checklist will be empty.")
        print("=" * 60)
    
    # Initialize data files
    init_data_files()
    
    # Run Flask app
    print("=" * 60)
    print("QA Testing Checklist Application")
    print("=" * 60)
    print("Starting Flask server...")
    print("Access the application at: http://127.0.0.1:10101")
    print("Press CTRL+C to quit")
    print("=" * 60)

    app.run(debug=False, host='127.0.0.1', port=10101)