# Gemini UI Design Skill

Use Gemini CLI for graphics, photos, image analysis, and UI design tasks.

## When to Use This Skill

- Generating UI mockups or design concepts
- Analyzing screenshots or images
- Creating visual assets descriptions
- Getting feedback on UI/UX designs
- Generating image descriptions for accessibility
- Creating color palette suggestions
- Analyzing competitor UIs

## Prerequisites

Authentication options:

**Option 1: API Key** - Add to root `.env` file:

```bash
GEMINI_API_KEY=your_api_key_here
```

**Option 2: Google Account** - Run `gemini` in terminal and login with your Google account (requires Gemini Advanced subscription)

## Calling Gemini from Claude

Use the Bash tool to invoke Gemini CLI for visual/design tasks:

### Basic Text Query

```bash
gemini -p "Describe a modern dark theme UI for a media management dashboard"
```

### Analyze an Image

```bash
gemini -p "Analyze this UI screenshot and suggest improvements" -f /path/to/screenshot.png
```

### Generate UI Descriptions

```bash
gemini -p "Create a detailed UI specification for a movie card component with poster, title, rating, and action buttons"
```

### Get Color Palette Suggestions

```bash
gemini -p "Suggest a color palette for a media streaming app. Include hex codes and usage guidelines"
```

## Common Use Cases

### 1. UI Component Design

```bash
gemini -p "Design a responsive navigation sidebar for a media library app. Include:
- Collapsible sections
- Icon suggestions
- Active state styling
- Dark/light theme considerations"
```

### 2. Screenshot Analysis

```bash
gemini -p "Analyze this screenshot and identify:
1. Usability issues
2. Accessibility concerns
3. Visual hierarchy problems
4. Suggested improvements" -f screenshot.png
```

### 3. Design System Suggestions

```bash
gemini -p "Create a design system specification for a media management app including:
- Typography scale
- Spacing system
- Border radius conventions
- Shadow levels"
```

### 4. Accessibility Review

```bash
gemini -p "Review this UI design for WCAG 2.1 AA compliance. Check:
- Color contrast ratios
- Focus indicators
- Touch target sizes
- Screen reader considerations" -f design.png
```

## Integration with Development

After getting Gemini's design suggestions, implement them using:

1. **React Components** - Create components in `autoarr/ui/src/components/`
2. **Tailwind CSS** - Use utility classes for styling
3. **shadcn/ui** - Leverage existing component library

## Example Workflow

1. **Get Design Concept**

   ```bash
   gemini -p "Design a movie details page with poster, synopsis, cast, and streaming options"
   ```

2. **Refine Based on Feedback**

   ```bash
   gemini -p "The movie details page needs to be more compact. Suggest a card-based layout instead"
   ```

3. **Get Implementation Details**

   ```bash
   gemini -p "Provide Tailwind CSS classes for implementing this card layout with dark theme"
   ```

4. **Implement in Code**
   - Create React component
   - Apply suggested styles
   - Add responsive breakpoints

## Limitations

- Gemini cannot directly create or edit files
- Image generation requires separate tools
- Always validate suggestions against project design system
- Consider performance implications of complex designs

## Best Practices

1. **Be Specific** - Provide context about the app and target users
2. **Include Constraints** - Mention existing design system, brand colors, etc.
3. **Iterate** - Use follow-up prompts to refine designs
4. **Validate** - Test suggestions against accessibility standards
5. **Document** - Save successful design patterns for reuse
