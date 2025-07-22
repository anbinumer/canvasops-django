# Cursor AI Implementation Guide: LTI Find & Replace Tool

## Objective
Create a production-ready Find & Replace tool within the CanvasOps Django LTI application that follows Canvas API-constrained human-centered design principles.

## Core Requirements

### 1. Django Integration
- Create new tool view in `tools/views.py`
- Add URL route for find-replace tool
- Integrate with existing LTI session management
- Use Canvas API credentials from LTI launch

### 2. Human-Centered UI/UX Flow

#### Step 1: Content Type Selection
```html
<div class="content-type-selector">
  <h3>What would you like to find?</h3>
  <div class="content-types">
    <button class="type-btn" data-type="url">
      🔗 URLs
      <span class="help-text">Web links, Canvas course URLs</span>
    </button>
    <button class="type-btn" data-type="text">
      📝 Text Content
      <span class="help-text">Specific words or phrases</span>
    </button>
    <button class="type-btn" data-type="iframe">
      🖼️ Embedded Content
      <span class="help-text">Videos, external tools</span>
    </button>
  </div>
  
  <div class="search-inputs" id="search-inputs">
    <!-- Dynamic inputs based on selection -->
  </div>
</div>
```

#### Step 2: Scope Definition with Emotional Support
```html
<div class="scope-selection">
  <h3>Where should I look? <span class="reassurance">I'll scan carefully for you</span></h3>
  
  <div class="content-areas">
    <label><input type="checkbox" checked> Pages</label>
    <label><input type="checkbox" checked> Syllabus</label>
    <label><input type="checkbox"> Assignments</label>
    <label><input type="checkbox"> Discussions</label>
    <label><input type="checkbox"> Quizzes</label>
    <label><input type="checkbox"> Announcements</label>
    <label><input type="checkbox"> Modules</label>
  </div>
  
  <div class="course-scope">
    <h4>Course Scope</h4>
    <label><input type="radio" name="scope" value="current" checked> Current course only</label>
    <label><input type="radio" name="scope" value="multiple"> Select specific courses</label>
    <label><input type="radio" name="scope" value="subaccount"> Entire subaccount</label>
  </div>
</div>
```

#### Step 3: Environment & Action Selection
```html
<div class="environment-action">
  <div class="environment-choice">
    <h3>Testing Environment</h3>
    <label><input type="radio" name="env" value="beta" checked> 
      Beta Instance <span class="recommended">Recommended</span>
      <div class="help">Safe testing - refreshed weekly from production</div>
    </label>
    <label><input type="radio" name="env" value="production"> 
      Production <span class="warning">Live Changes</span>
    </label>
  </div>
  
  <div class="action-choice">
    <h3>What would you like to do?</h3>
    <label><input type="radio" name="action" value="preview" checked> 
      Preview Only <span class="safe">Safe</span>
      <div class="help">Generate report of what would change</div>
    </label>
    <label><input type="radio" name="action" value="replace"> 
      Find and Replace
    </label>
    <label><input type="radio" name="action" value="delete"> 
      Find and Delete <span class="destructive">⚠️ Irreversible</span>
    </label>
  </div>
</div>
```

### 3. Backend Implementation

#### Core Class Structure
```python
# tools/find_replace.py
class LTIFindReplaceService:
    def __init__(self, canvas_url, api_token, is_beta=False):
        self.base_url = f"https://{canvas_url.replace('https://', '')}"
        if is_beta:
            self.base_url = self.base_url.replace('.instructure.com', '.beta.instructure.com')
        self.api_token = api_token
        self.dry_run = True  # Default to safe mode
    
    def scan_content(self, course_ids, content_types, search_targets):
        """Scan for content without making changes"""
        pass
    
    def preview_changes(self, scan_results, replacements):
        """Show what would be changed"""
        pass
    
    def apply_changes(self, course_ids, changes, dry_run=True):
        """Apply changes with safety checks"""
        pass
```

#### Django Views
```python
# tools/views.py
@require_http_methods(["GET", "POST"])
def find_replace_tool(request):
    if request.method == "GET":
        return render(request, 'tools/find_replace.html', {
            'canvas_user_id': request.session.get('canvas_user_id'),
            'canvas_course_id': request.session.get('canvas_course_id'),
            'canvas_url': request.session.get('canvas_url'),
        })
    
    # POST: Process find/replace request
    return handle_find_replace_request(request)

def handle_find_replace_request(request):
    # Extract form data with validation
    # Create service instance
    # Execute based on action type
    # Return results with proper error handling
    pass
```

### 4. Human-Centered Design Implementation

#### Emotional Support Language
```python
MESSAGES = {
    'scanning': "I'm carefully scanning your content...",
    'found_items': "Great! I found {count} items that match your search.",
    'no_matches': "No matches found - your content looks good!",
    'changes_applied': "✅ Successfully updated {count} items. Your course is ready!",
    'preview_ready': "Here's what I would change. Review and confirm when ready.",
}
```

#### Progress Communication
```javascript
// Real-time progress updates
function updateProgress(step, total, message) {
    document.getElementById('progress-bar').style.width = `${(step/total)*100}%`;
    document.getElementById('progress-message').textContent = message;
}
```

#### Trust-Building Features
```python
def generate_change_preview(self, findings):
    """Generate detailed preview with context"""
    return {
        'total_matches': len(findings),
        'by_location': group_by_location(findings),
        'sample_changes': findings[:5],  # Show first 5 as examples
        'scope_summary': f"Will scan {self.get_scope_description()}",
        'safety_note': "No changes will be made until you confirm."
    }
```

### 5. Canvas API Integration Patterns

Use existing script patterns for:
- Paginated API requests
- Content scanning (syllabus, pages, assignments, etc.)
- Error handling and rate limiting
- Report generation

### 6. Required Files to Create/Modify

1. `tools/find_replace.py` - Core service class
2. `tools/views.py` - Add find_replace_tool view
3. `tools/urls.py` - Add route
4. `templates/tools/find_replace.html` - Main interface
5. `static/js/find_replace.js` - Frontend interactions
6. `static/css/find_replace.css` - Styling

### 7. Key Design Principles to Follow

- **Start with preview/beta by default** (safe first)
- **Show progress and context** throughout process
- **Use reassuring, supportive language**
- **Require explicit confirmation** for destructive actions
- **Provide detailed reports** for audit trails
- **Handle errors gracefully** with helpful messages

### 8. Success Criteria

- Tool launches seamlessly from LTI dashboard
- Users feel confident about what will happen
- Preview mode works perfectly before any changes
- Comprehensive reports generated for all actions
- Error states handled with helpful guidance
- UI feels native to Canvas design system

## Status Update (2025)
- The Find & Replace tool is now live, styled with ACU branding, and fully integrated with LTI session management.
- Backend service, Django view, and URL route are implemented and tested.
- UI uses Tailwind CSS and human-centered feedback language.
- Default mode is preview/safe for user reassurance.
- Workflow includes testing in Canvas Beta before production.

## Implementation Notes

- Leverage existing script logic from the provided examples
- Focus on user experience over technical complexity
- Test thoroughly in beta environment first
- Generate detailed documentation for users
- Consider workflow integration with existing Canvas processes