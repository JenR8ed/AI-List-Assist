💡 What: Added ARIA attributes, keyboard interaction, and explicit focus states to the drag-and-drop upload areas and buttons in `index.html` and `dashboard.html`.
🎯 Why: Custom `div` elements acting as buttons (like the upload area) are inaccessible to keyboard and screen reader users by default. Standard buttons were also missing clear visual focus indicators during keyboard navigation.
📸 Before/After: The upload area now displays a clear blue outline with a 2px offset when navigated to via the `Tab` key, and triggers the file dialogue upon pressing `Enter` or `Space`.
♿ Accessibility:
  - Added `tabindex="0"`, `role="button"`, and `aria-label` to the `.upload-area` and `.upload-section`.
  - Added `keydown` event listeners to trigger clicks on `Enter` or `Space`.
  - Added explicit `:focus-visible` CSS rules for upload areas, tabs, and buttons to provide clear keyboard focus rings.
