# User Stories

## Feature 1: Tags and labels

### Story 1
As a user, I want to create and apply tags to tasks so I can group related work.

**Acceptance criteria:**
- I can create a non-blank tag.
- I can select one or more existing tags while creating or editing a task.
- Selected tags are returned by the API and displayed on the task card.

### Story 2
As a user, I want to view all available tags so I can choose consistent labels.

**Acceptance criteria:**
- The board loads the available tags.
- The task form offers the available tags for selection.

### Story 3
As a user, I want to filter tasks by tag so I can focus on a category of work.

**Acceptance criteria:**
- Selecting a tag shows only tasks containing that tag.
- Clearing the filter shows tasks from all tags.

**Corrected AI assumption:** AI initially suggested a full tag-management area with rename and delete operations. That was rejected because this assignment needs create, apply, display, and filter only.

## Feature 2: Due dates and overdue filter

### Story 1
As a user, I want to assign an optional due date to a task so I know when it needs to be completed.

**Acceptance criteria:**
- The task form accepts a valid calendar date.
- The date can be added, changed, or cleared during editing.
- Invalid date input is rejected with HTTP 422.

### Story 2
As a user, I want to see which tasks are overdue so I can prioritize urgent work.

**Acceptance criteria:**
- A task is overdue only when its due date is before today and its status is not `Done`.
- Tasks due today, tasks without a due date, and completed past-due tasks are not overdue.
- Overdue tasks show an overdue indicator on their cards.

### Story 3
As a user, I want to filter the board to overdue tasks so I can focus on follow-up.

**Acceptance criteria:**
- The overdue filter returns only incomplete tasks whose due date has passed.
- Clearing the filter restores the normal board results.

**Corrected AI assumption:** AI treated a due date equal to today as overdue in an initial interpretation. The final rule uses `due_date < today`, so due-today tasks remain current.