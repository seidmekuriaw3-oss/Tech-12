import re
import os
import sys

def fix_app_routes():
    """Fix missing admin routes in app.py"""
    
    app_file = 'app.py'
    
    # Check if app.py exists
    if not os.path.exists(app_file):
        print(f"❌ {app_file} not found in current directory")
        return False
    
    # Read the current content
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # ============================================================
    # 1. CHECK AND FIX ADMIN/ADS/ADD ROUTE
    # ============================================================
    
    if '/admin/ads/add' not in content:
        print("📝 Adding missing /admin/ads/add route...")
        
        new_route = '''
# ------------------------------------------------------------------
# Add Advertisement Route
# ------------------------------------------------------------------
@app.route('/admin/ads/add', methods=['GET', 'POST'])
def admin_add_ad():
    """
    Add new advertisement - GET: Show form, POST: Process data.
    """
    if not session.get('admin'):
        flash('Please log in to access admin panel.', 'warning')
        return redirect(url_for('admin.login'))
    
    lang = get_lang()
    t = TEXTS.get(lang, TEXTS['am'])
    
    if request.method == 'POST':
        try:
            ad_text = request.form.get('ad_text', '').strip()
            
            if not ad_text:
                flash('Please enter advertisement text.', 'error')
                return redirect(url_for('admin_ads'))
            
            # Handle media upload
            media_file = request.files.get('media')
            media_filename = ''
            
            if media_file and media_file.filename:
                if allowed_file(media_file.filename):
                    # Save file to ads subfolder
                    ext = media_file.filename.rsplit('.', 1)[1].lower()
                    media_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ads')
                    os.makedirs(upload_path, exist_ok=True)
                    media_file.save(os.path.join(upload_path, media_filename))
                    app.logger.info(f"Ad media saved: {media_filename}")
                else:
                    flash('Invalid file type. Please upload an image or video.', 'error')
                    return redirect(url_for('admin_ads'))
            
            # Save to database
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ads (text, media) VALUES (?, ?)", (ad_text, media_filename))
            conn.commit()
            conn.close()
            
            app.logger.info(f"New advertisement added: {ad_text[:50]}...")
            flash('Advertisement added successfully!', 'success')
            return redirect(url_for('admin_ads'))
            
        except Exception as e:
            app.logger.error(f"Error adding advertisement: {str(e)}")
            flash('Error adding advertisement. Please try again.', 'error')
            return redirect(url_for('admin_ads'))
    
    # GET request - show form
    return render_template('admin/ads/add.html', lang=lang, t=t)
'''
        
        # Find a good insertion point (before if __name__ or at end of admin routes)
        if 'if __name__ ==' in content:
            content = content.replace('if __name__ ==', new_route + '\n\nif __name__ ==')
            modified = True
        elif '# ==================== MAIN ENTRY POINT ====================' in content:
            content = content.replace('# ==================== MAIN ENTRY POINT ====================', 
                                    new_route + '\n\n# ==================== MAIN ENTRY POINT ====================')
            modified = True
        else:
            # Append at the end
            content += '\n' + new_route
            modified = True
        
        print("   ✅ /admin/ads/add route added")
    else:
        # Check if route needs improvement
        if 'media' not in content or 'allowed_file' not in content[content.find('/admin/ads/add'):content.find('/admin/ads/add') + 2000]:
            print("⚠️  Existing /admin/ads/add route may need media upload support")
        else:
            print("✅ /admin/ads/add route already exists")
    
    # ============================================================
    # 2. CHECK AND FIX ADMIN/ADS/DELETE ROUTE
    # ============================================================
    
    if '/admin/ads/delete' not in content:
        print("📝 Adding missing /admin/ads/delete route...")
        
        delete_route = '''
# ------------------------------------------------------------------
# Delete Advertisement Route
# ------------------------------------------------------------------
@app.route('/admin/ads/delete/<int:aid>')
def admin_delete_ad(aid):
    """
    Delete advertisement - Remove ad from database and delete media.
    
    Args:
        aid (int): Advertisement ID
    """
    if not session.get('admin'):
        flash('Please log in to access admin panel.', 'warning')
        return redirect(url_for('admin.login'))
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get ad media before deleting
        cursor.execute("SELECT text, media FROM ads WHERE id = ?", (aid,))
        ad = cursor.fetchone()
        
        if ad:
            # Delete media file if exists
            if ad[1]:
                media_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ads', ad[1])
                if os.path.exists(media_path):
                    os.remove(media_path)
                    app.logger.info(f"Deleted ad media: {ad[1]}")
            
            # Delete from database
            cursor.execute("DELETE FROM ads WHERE id = ?", (aid,))
            conn.commit()
            
            app.logger.info(f"Advertisement deleted: {ad[0][:50]}...")
            flash('Advertisement deleted successfully!', 'success')
        else:
            flash('Advertisement not found.', 'error')
        
        conn.close()
        return redirect(url_for('admin_ads'))
    
    except Exception as e:
        app.logger.error(f"Error deleting advertisement {aid}: {str(e)}")
        flash('Error deleting advertisement.', 'error')
        return redirect(url_for('admin_ads'))
'''
        
        # Find insertion point
        if 'if __name__ ==' in content:
            content = content.replace('if __name__ ==', delete_route + '\n\nif __name__ ==')
            modified = True
        elif '# ==================== MAIN ENTRY POINT ====================' in content:
            content = content.replace('# ==================== MAIN ENTRY POINT ====================', 
                                    delete_route + '\n\n# ==================== MAIN ENTRY POINT ====================')
            modified = True
        else:
            content += '\n' + delete_route
            modified = True
        
        print("   ✅ /admin/ads/delete route added")
    else:
        # Check if delete route includes media deletion
        if 'media' not in content[content.find('/admin/ads/delete'):content.find('/admin/ads/delete') + 1500]:
            print("⚠️  Existing delete route may not delete media files")
        else:
            print("✅ /admin/ads/delete route already exists")
    
    # ============================================================
    # 3. CHECK AND FIX ADMIN/ADS/EDIT ROUTE (if missing)
    # ============================================================
    
    if '/admin/ads/edit' not in content:
        print("📝 Adding missing /admin/ads/edit route...")
        
        edit_route = '''
# ------------------------------------------------------------------
# Edit Advertisement Route
# ------------------------------------------------------------------
@app.route('/admin/ads/edit/<int:aid>', methods=['GET', 'POST'])
def admin_edit_ad(aid):
    """
    Edit advertisement - GET: Show form, POST: Update data.
    
    Args:
        aid (int): Advertisement ID
    """
    if not session.get('admin'):
        flash('Please log in to access admin panel.', 'warning')
        return redirect(url_for('admin.login'))
    
    lang = get_lang()
    t = TEXTS.get(lang, TEXTS['am'])
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, text, media FROM ads WHERE id = ?", (aid,))
        ad = cursor.fetchone()
        conn.close()
        
        if not ad:
            flash('Advertisement not found.', 'error')
            return redirect(url_for('admin_ads'))
        
        if request.method == 'POST':
            try:
                ad_text = request.form.get('ad_text', '').strip()
                
                if not ad_text:
                    flash('Please enter advertisement text.', 'error')
                    return redirect(url_for('admin_edit_ad', aid=aid))
                
                # Handle media upload
                media_file = request.files.get('media')
                media_filename = ad[2]  # Keep existing media
                
                if media_file and media_file.filename:
                    if allowed_file(media_file.filename):
                        # Delete old media if exists
                        if ad[2]:
                            old_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ads', ad[2])
                            if os.path.exists(old_path):
                                os.remove(old_path)
                                app.logger.info(f"Deleted old ad media: {ad[2]}")
                        
                        # Save new media
                        ext = media_file.filename.rsplit('.', 1)[1].lower()
                        media_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ads')
                        os.makedirs(upload_path, exist_ok=True)
                        media_file.save(os.path.join(upload_path, media_filename))
                        app.logger.info(f"Ad media updated: {media_filename}")
                    else:
                        flash('Invalid file type. Please upload an image or video.', 'error')
                        return redirect(url_for('admin_edit_ad', aid=aid))
                
                # Update database
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("UPDATE ads SET text = ?, media = ? WHERE id = ?", (ad_text, media_filename, aid))
                conn.commit()
                conn.close()
                
                app.logger.info(f"Advertisement updated: ID {aid}")
                flash('Advertisement updated successfully!', 'success')
                return redirect(url_for('admin_ads'))
                
            except Exception as e:
                app.logger.error(f"Error updating advertisement: {str(e)}")
                flash('Error updating advertisement.', 'error')
                return redirect(url_for('admin_edit_ad', aid=aid))
        
        return render_template('admin/ads/edit.html', ad=ad, lang=lang, t=t)
    
    except Exception as e:
        app.logger.error(f"Error loading advertisement {aid}: {str(e)}")
        flash('Error loading advertisement.', 'error')
        return redirect(url_for('admin_ads'))
'''
        
        if 'if __name__ ==' in content:
            content = content.replace('if __name__ ==', edit_route + '\n\nif __name__ ==')
            modified = True
        else:
            content += '\n' + edit_route
            modified = True
        
        print("   ✅ /admin/ads/edit route added")
    else:
        print("✅ /admin/ads/edit route already exists")
    
    # ============================================================
    # 4. CREATE MISSING TEMPLATES
    # ============================================================
    
    templates_dir = 'templates/admin/ads'
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir, exist_ok=True)
        print(f"📁 Created directory: {templates_dir}")
    
    # Create add.html template if missing
    add_template_path = os.path.join(templates_dir, 'add.html')
    if not os.path.exists(add_template_path):
        print("📝 Creating add.html template...")
        add_template = '''{% extends "admin/base.html" %}

{% block title %}Add Advertisement{% endblock %}

{% block content %}
<div class="container">
    <div class="card">
        <div class="card-header">
            <h2>Add New Advertisement</h2>
        </div>
        <div class="card-body">
            <form method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="ad_text">Advertisement Text</label>
                    <textarea class="form-control" id="ad_text" name="ad_text" rows="3" required></textarea>
                </div>
                
                <div class="form-group">
                    <label for="media">Media (Image or Video - Optional)</label>
                    <input type="file" class="form-control-file" id="media" name="media" accept="image/*,video/*">
                    <small class="form-text text-muted">
                        Supported formats: PNG, JPG, JPEG, GIF, WEBP, MP4, WEBM, MOV
                    </small>
                </div>
                
                <button type="submit" class="btn btn-primary">Add Advertisement</button>
                <a href="{{ url_for('admin_ads') }}" class="btn btn-secondary">Cancel</a>
            </form>
        </div>
    </div>
</div>
{% endblock %}
'''
        with open(add_template_path, 'w', encoding='utf-8') as f:
            f.write(add_template)
        print("   ✅ add.html created")
    
    # Create edit.html template if missing
    edit_template_path = os.path.join(templates_dir, 'edit.html')
    if not os.path.exists(edit_template_path):
        print("📝 Creating edit.html template...")
        edit_template = '''{% extends "admin/base.html" %}

{% block title %}Edit Advertisement{% endblock %}

{% block content %}
<div class="container">
    <div class="card">
        <div class="card-header">
            <h2>Edit Advertisement</h2>
        </div>
        <div class="card-body">
            <form method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="ad_text">Advertisement Text</label>
                    <textarea class="form-control" id="ad_text" name="ad_text" rows="3" required>{{ ad[1] }}</textarea>
                </div>
                
                <div class="form-group">
                    <label>Current Media</label>
                    {% if ad[2] %}
                        {% if ad[2].endswith(('.mp4', '.webm', '.mov')) %}
                            <video controls style="max-width: 300px;">
                                <source src="{{ url_for('static', filename='uploads/ads/' + ad[2]) }}">
                            </video>
                        {% else %}
                            <img src="{{ url_for('static', filename='uploads/ads/' + ad[2]) }}" style="max-width: 300px;">
                        {% endif %}
                        <br>
                    {% else %}
                        <p>No media attached</p>
                    {% endif %}
                </div>
                
                <div class="form-group">
                    <label for="media">Replace Media (Optional)</label>
                    <input type="file" class="form-control-file" id="media" name="media" accept="image/*,video/*">
                    <small class="form-text text-muted">
                        Leave empty to keep current media
                    </small>
                </div>
                
                <button type="submit" class="btn btn-primary">Update Advertisement</button>
                <a href="{{ url_for('admin_ads') }}" class="btn btn-secondary">Cancel</a>
            </form>
        </div>
    </div>
</div>
{% endblock %}
'''
        with open(edit_template_path, 'w', encoding='utf-8') as f:
            f.write(edit_template)
        print("   ✅ edit.html created")
    
    # Create index.html template if missing (improved version)
    index_template_path = 'templates/admin/ads/index.html'
    if not os.path.exists(index_template_path):
        print("📝 Creating improved index.html template...")
        index_template = '''{% extends "admin/base.html" %}

{% block title %}Manage Advertisements{% endblock %}

{% block content %}
<div class="container">
    <div class="card">
        <div class="card-header">
            <h2>Advertisement Management</h2>
            <a href="{{ url_for('admin_add_ad') }}" class="btn btn-primary">+ Add New Ad</a>
        </div>
        <div class="card-body">
            {% if ads %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Text</th>
                                <th>Media</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for ad in ads %}
                            <tr>
                                <td>{{ ad[0] }}</td>
                                <td>{{ ad[1][:100] }}{% if ad[1]|length > 100 %}...{% endif %}</td>
                                <td>
                                    {% if ad[2] %}
                                        {% if ad[2].endswith(('.mp4', '.webm', '.mov')) %}
                                            <span class="badge badge-info">Video</span>
                                        {% else %}
                                            <span class="badge badge-success">Image</span>
                                        {% endif %}
                                    {% else %}
                                        <span class="badge badge-secondary">Text only</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <a href="{{ url_for('admin_edit_ad', aid=ad[0]) }}" class="btn btn-sm btn-warning">Edit</a>
                                    <a href="{{ url_for('admin_delete_ad', aid=ad[0]) }}" class="btn btn-sm btn-danger" onclick="return confirm('Are you sure you want to delete this ad?')">Delete</a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <div class="alert alert-info">
                    No advertisements found. <a href="{{ url_for('admin_add_ad') }}">Create your first ad</a>
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
'''
        with open(index_template_path, 'w', encoding='utf-8') as f:
            f.write(index_template)
        print("   ✅ index.html created/improved")
    
    # ============================================================
    # 5. SAVE CHANGES IF ANY
    # ============================================================
    
    if modified:
        with open(app_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("\n✅ All changes saved to app.py")
        print("⚠️  Please restart your Flask application for changes to take effect.")
    else:
        print("\n✅ No changes needed - all routes are present")
    
    # ============================================================
    # 6. VERIFICATION
    # ============================================================
    
    print("\n" + "=" * 60)
    print("🔍 VERIFICATION")
    print("=" * 60)
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    routes_to_check = [
        '/admin/ads/add',
        '/admin/ads/delete',
        '/admin/ads/edit'
    ]
    
    for route in routes_to_check:
        if route in content:
            print(f"✅ {route} - Found")
        else:
            print(f"❌ {route} - Missing")
    
    templates_to_check = [
        'templates/admin/ads/index.html',
        'templates/admin/ads/add.html',
        'templates/admin/ads/edit.html'
    ]
    
    for template in templates_to_check:
        if os.path.exists(template):
            print(f"✅ {template} - Found")
        else:
            print(f"⚠️  {template} - Not found")
    
    print("=" * 60)
    
    return True


def verify_database_structure():
    """Verify and update database structure for ads table"""
    import sqlite3
    from config import Config
    
    db_path = Config.DATABASE_PATH if hasattr(Config, 'DATABASE_PATH') else 'ethiosadat.db'
    
    if not os.path.exists(db_path):
        print(f"⚠️  Database not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if media column exists in ads table
        cursor.execute("PRAGMA table_info(ads)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'media' not in columns:
            print("📝 Adding media column to ads table...")
            cursor.execute("ALTER TABLE ads ADD COLUMN media TEXT")
            conn.commit()
            print("   ✅ media column added")
        else:
            print("✅ media column already exists")
        
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Could not verify database: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔧 ETHIOSADAT ROUTE FIXER")
    print("=" * 60)
    
    # Fix routes in app.py
    success = fix_app_routes()
    
    # Verify database structure
    print("\n📂 Verifying database structure...")
    verify_database_structure()
    
    print("\n✨ Done!")