# Raw Idea: Optional Scanning Module

## Source
Roadmap Item #7

## Description
Create a minimal venusian-inspired scanning system for auto-discovery of services using modern Python 3.12+ package discovery, simplified to work only with svcs-di registry without categories or complex features. Keep this as an optional module separate from core. Write tests and examples that show making a `svcs.Registry` as part of a decorator and passing it to the wrapped registrant. Look in Hopscotch for an example decorator. We have a local venusian checkout in `/Users/pauleveritt/PycharmProjects/venusian`.

## Size Estimate
Large (L)

## Status
Not started

## Dependencies
- Requires items 1-6 from roadmap (all completed)
- Reference implementation: Local venusian checkout at `/Users/pauleveritt/PycharmProjects/venusian`
- Reference example: Hopscotch decorator examples

## Key Constraints
- Must remain optional (separate from core)
- Simplified compared to venusian (no categories or complex features)
- Works only with svcs-di registry
- Uses modern Python 3.12+ package discovery
