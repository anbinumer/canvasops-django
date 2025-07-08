# canvasops-django

**Project Status:** LTI 1.3 launch and authentication working end-to-end. See PRD and lti_setup_guide.md for lessons learned, best practices, and onboarding tips for future LTI tool development.

## Troubleshooting

- If you encounter a 500 error on a Django view that renders a template, check for missing context variables (especially session data) and provide defaults in the view.
- Ensure there is no ambiguity between project-level and app-level templates with the same name. Remove or rename unused templates to avoid confusion.