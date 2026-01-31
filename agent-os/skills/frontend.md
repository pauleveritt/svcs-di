---
description:
  Frontend development standards for UI components, CSS, accessibility, and
  responsive design. Use this when building web interfaces or reviewing
  frontend code.
---

# Frontend Development Standards

## UI Component Best Practices

- **Single Responsibility**: Each component should have one clear purpose and do it well
- **Reusability**: Design components to be reused across different contexts with configurable props
- **Composability**: Build complex UIs by combining smaller, simpler components rather than monolithic structures
- **Clear Interface**: Define explicit, well-documented props with sensible defaults for ease of use
- **Encapsulation**: Keep internal implementation details private and expose only necessary APIs
- **Consistent Naming**: Use clear, descriptive names that indicate the component's purpose
- **Minimal Props**: Keep the number of props manageable; if a component needs many props, consider composition or splitting it
- **Documentation**: Document component usage, props, and provide examples for easier adoption

## CSS Best Practices

- **Consistent Methodology**: Apply and stick to the project's consistent CSS methodology (Tailwind, BEM, utility classes, CSS modules, etc.) across the entire project
- **Avoid Overriding Framework Styles**: Work with your framework's patterns rather than fighting against them with excessive overrides
- **Maintain Design System**: Establish and document design tokens (colors, spacing, typography) for consistency
- **Minimize Custom CSS**: Leverage framework utilities and components to reduce custom CSS maintenance burden
- **Performance Considerations**: Optimize for production with CSS purging/tree-shaking to remove unused styles

## Accessibility Best Practices

- **Semantic HTML**: Use appropriate HTML elements (nav, main, button, etc.) that convey meaning to assistive technologies
- **Keyboard Navigation**: Ensure all interactive elements are accessible via keyboard with visible focus indicators
- **Color Contrast**: Maintain sufficient contrast ratios (4.5:1 for normal text) and don't rely solely on color to convey information
- **Alternative Text**: Provide descriptive alt text for images and meaningful labels for all form inputs
- **Screen Reader Testing**: Test and verify that all views are accessible on screen reading devices
- **ARIA When Needed**: Use ARIA attributes to enhance complex components when semantic HTML isn't sufficient
- **Logical Heading Structure**: Use heading levels (h1-h6) in proper order to create a clear document outline
- **Focus Management**: Manage focus appropriately in dynamic content, modals, and single-page applications

## Responsive Design Best Practices

- **Mobile-First Development**: Start with mobile layout and progressively enhance for larger screens
- **Standard Breakpoints**: Consistently use standard breakpoints across the application (mobile, tablet, desktop)
- **Fluid Layouts**: Use percentage-based widths and flexible containers that adapt to screen size
- **Relative Units**: Prefer rem/em units over fixed pixels for better scalability and accessibility
- **Test Across Devices**: Test and verify UI changes across multiple screen sizes from mobile to tablet to desktop
- **Touch-Friendly Design**: Ensure tap targets are appropriately sized (minimum 44x44px) for mobile users
- **Performance on Mobile**: Optimize images and assets for mobile network conditions and smaller screens
- **Readable Typography**: Maintain readable font sizes across all breakpoints without requiring zoom
- **Content Priority**: Show the most important content first on smaller screens through thoughtful layout decisions

## Anti-Patterns

- **God components**: Components that do too much and have dozens of props
- **Prop drilling**: Passing props through many layers instead of using composition
- **Inline styles everywhere**: Using style attributes instead of CSS classes
- **Ignoring accessibility**: Building UIs that only work with mouse interaction
- **Fixed dimensions**: Using fixed pixel widths that break on different screen sizes
- **Missing focus states**: Interactive elements without visible focus indicators
- **Non-semantic markup**: Using divs and spans where semantic elements would work
- **Over-engineering**: Adding complex state management for simple UI needs
- **Inconsistent spacing**: Using arbitrary margin/padding values instead of design tokens
- **Missing loading states**: Not handling async operations with proper feedback

## Related Skills

- [tdom](tdom.md) - Building UI components with tdom
- [testing](testing/testing.md) - Testing UI components
- [python](python.md) - Python development standards
