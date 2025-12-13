# CommunityAdmin Cleanup Implementation Plan

## Phase 1: Code Cleanup (2 hours)

### 1.1 Remove CommunityAdmin imports
**Files to update:**
- `src/wxcloudrun/__init__.py` - Line 49
- `src/wxcloudrun/views/community.py` - Line 11
- `src/wxcloudrun/views/user.py` - Line 457
- `src/wxcloudrun/community_service.py` - Line 11

**Action:**
```python
# Remove these imports
from wxcloudrun.model import CommunityAdmin
```

### 1.2 Remove CommunityAdmin endpoints
**File:** `src/wxcloudrun/views/community.py`

**Endpoints to remove:**
1. Line 332: `@app.route('/api/communities/<int:community_id>/admins', methods=['GET'])`
2. Line 375: `@app.route('/api/communities/<int:community_id>/admins', methods=['POST'])`
3. Line 449: `@app.route('/api/communities/<int:community_id>/admins/<int:target_user_id>', methods=['DELETE'])`
4. Line 546: `@app.route('/api/communities/<int:community_id>/users/<int:target_user_id>/set-admin', methods=['POST'])`
5. Line 977: `@app.route('/api/communities/<int:community_id>/admins/<int:user_id>/role', methods=['PUT'])`

**Action:** Remove entire function definitions for these endpoints

### 1.3 Update user search logic
**File:** `src/wxcloudrun/views/user.py`
**Lines:** 457-459

**Current code:**
```python
if scope == 'community':
    from wxcloudrun.model import CommunityAdmin
    query = query.join(CommunityAdmin, User.user_id == CommunityAdmin.user_id).filter(
        CommunityAdmin.community_id == int(community_id)
    )
```

**New code:**
```python
if scope == 'community':
    from wxcloudrun.model_community_extensions import CommunityStaff
    query = query.join(CommunityStaff, User.user_id == CommunityStaff.user_id).filter(
        CommunityStaff.community_id == int(community_id)
    )
```

## Phase 2: Service Layer Updates (1 hour)

### 2.1 Update community_service.py
**File:** `src/wxcloudrun/community_service.py`

**Actions:**
1. Remove CommunityAdmin import (line 11)
2. Update `add_community_admin()` method:
   - Remove CommunityAdmin creation (lines 51-57)
   - Keep only CommunityStaff creation
3. Update `remove_community_admin()` method:
   - Remove CommunityAdmin deletion (lines 243-245)
   - Keep only CommunityStaff deletion
4. Update `search_community_users()` method:
   - Replace CommunityAdmin query with CommunityStaff

## Phase 3: Model Cleanup (30 minutes)

### 3.1 Remove CommunityAdmin class
**File:** `src/wxcloudrun/model.py`
**Lines:** ~629-679

**Action:** Delete entire CommunityAdmin class definition

### 3.2 Update Community model relationship
**File:** `src/wxcloudrun/model.py`
**Line:** 599

**Remove:**
```python
admins = db.relationship('CommunityAdmin', backref='community', lazy='dynamic')
```

### 3.3 Drop database table
**SQL command:**
```sql
DROP TABLE IF EXISTS community_admins;
```

## Phase 4: Test Updates (2-3 hours)

### 4.1 Update test files
**Files to update:**
- `tests/e2e/test_set_admin_api.py` - Remove or update tests
- `tests/unit/test_community_role_update.py` - Remove or update tests
- `tests/integration/test_community_integration.py` - Update integration tests
- `tests/unit/test_community.py` - Remove CommunityAdmin references

### 4.2 Remove CommunityAdmin from test imports
Update all test files to remove CommunityAdmin imports

### 4.3 Update test assertions
Change any assertions expecting CommunityAdmin behavior to expect CommunityStaff behavior

## Verification Steps

### After each phase:
1. Run unit tests: `make test-unit`
2. Check for import errors
3. Verify endpoints still work (where applicable)

### After completion:
1. Run full test suite: `make test-all`
2. Manual testing of CommunityStaff endpoints
3. Verify user search functionality
4. Check permission systems still work

## Rollback Plan

If issues arise:
1. Git revert to commit before cleanup
2. Restore community_admins table from backup if needed
3. Re-add CommunityAdmin imports and model

## Notes
- No data migration needed as CommunityStaff contains all necessary data
- CommunityStaff provides enhanced features (multi-community support)
- Some API clients will need to update to use new endpoints