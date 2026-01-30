# Implementation Plan - Authentication System

## Goal
Add password-based authentication to prevent unauthorized access and API abuse.

## Approach
Use Streamlit's `secrets` management with a simple login check.

## Proposed Changes

### 1. Update `app.py`
- Add login state management in `session_state`
- Create a login UI that appears before the main app
- Check credentials against Streamlit secrets
- Only render main app after successful login

### 2. Update Deployment Instructions
- Document how to add `AUTH_PASSWORD` to Streamlit Cloud secrets
- Add login credentials to local `.streamlit/secrets.toml` for development

## Security Benefits
- Prevents random users from consuming API quota
- Simple but effective for personal/small team use
- Password can be easily rotated in Streamlit Cloud settings

## Verification Plan
1. Test login flow locally with secrets.toml
2. Verify failed login attempts are blocked
3. Confirm successful login grants full access
