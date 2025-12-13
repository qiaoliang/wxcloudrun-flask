# CommunityAdmin Cleanup Design

## Overview
This document outlines the plan to remove the deprecated `CommunityAdmin` model from the SafeGuard backend system. The `CommunityStaff` model has already been implemented and provides enhanced functionality, making `CommunityAdmin` redundant.

## Current State Analysis

### CommunityAdmin Model (To Be Removed)
- Table: `community_admins`
- Roles: Numeric (1=primary, 2=normal)
- Features: Single community assignment per user
- Endpoints: 5 endpoints using this model

### CommunityStaff Model (Replacement)
- Table: `community_staff`
- Roles: String-based ("manager", "staff")
- Features: Multi-community support, scope field for staff responsibilities
- Endpoints: 3 endpoints already implemented

## Endpoints Mapping

### To Be Removed (CommunityAdmin):
1. `GET /api/communities/<id>/admins` - List community admins
2. `POST /api/communities/<id>/admins` - Add admin (legacy)
3. `DELETE /api/communities/<id>/admins/<user_id>` - Remove admin (legacy)
4. `POST /api/communities/<id>/users/<user_id>/set-admin` - Quick admin assignment
5. `PUT /api/communities/<id>/admins/<user_id>/role` - Update admin role

### Replacement Endpoints (CommunityStaff):
1. `GET /api/community/staff/list` - List staff members (with filtering)
2. `POST /api/community/add-staff` - Add staff member
3. `POST /api/community/remove-staff` - Remove staff member

### Missing Replacement:
- Update staff role endpoint (needs to be created)

## Implementation Plan

### Phase 1: Code Cleanup
1. Remove CommunityAdmin imports from:
   - `wxcloudrun/__init__.py`
   - `wxcloudrun/views/community.py`
   - `wxcloudrun/views/user.py`
   - `wxcloudrun/community_service.py`

2. Remove the 5 CommunityAdmin endpoints from `views/community.py`:
   - Lines 332, 375, 449, 546, 977

3. Update user search logic in `views/user.py`:
   - Replace CommunityAdmin join with CommunityStaff join

### Phase 2: Service Layer Updates
1. Update `community_service.py`:
   - Remove CommunityAdmin import
   - Remove CommunityAdmin creation in `add_community_admin()`
   - Update `search_community_users()` to use CommunityStaff

### Phase 3: Model Cleanup
1. Remove CommunityAdmin class from `model.py`:
   - Delete the entire class definition (lines ~629-679)
   - Remove `admins` relationship from Community model

2. Drop the database table:
   ```sql
   DROP TABLE IF EXISTS community_admins;
   ```

### Phase 4: Test Updates
1. Update or remove tests in:
   - `test_set_admin_api.py`
   - `test_community_role_update.py`
   - `test_community_integration.py`
   - `test_community.py`

## Risk Assessment

### Low Risk:
- CommunityStaff already handles all core functionality
- Permission systems already migrated to CommunityStaff
- No data migration needed

### Medium Risk:
- Some tests will fail and need updates
- API clients using old endpoints will need to update

### Mitigations:
- Comprehensive testing after each phase
- Clear documentation of endpoint changes
- Gradual rollout with monitoring

## Success Criteria
1. All CommunityAdmin references removed from code
2. CommunityStaff endpoints handle all use cases
3. Test suite passes with CommunityStaff only
4. No performance degradation
5. Documentation updated

## Timeline
- Phase 1: 2 hours
- Phase 2: 1 hour
- Phase 3: 30 minutes
- Phase 4: 2-3 hours
- Testing: 2 hours

**Total estimated time: 8-9 hours**

## Notes
- The system is already mostly migrated to CommunityStaff
- This cleanup removes redundant code rather than core functionality
- CommunityStaff provides better features (multi-community support, role clarity)