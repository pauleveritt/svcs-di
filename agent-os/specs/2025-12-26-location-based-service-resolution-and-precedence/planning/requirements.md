# Spec Requirements: Location-Based Service Resolution and Precedence

## Initial Description

Combining sections 8 "Location-Based Service Resolution" and 9 "Precedence" together.

The user wants to work on these two sections from their roadmap as a single feature specification.

From Roadmap:
- **Item 8:** Location-Based Service Resolution — Add location/path-based service resolution where services registered with a location (PurePath) are selected when the request location is relative to the registered location, enabling URL-based or hierarchical service selection. Allow this to be combined with `request` selection but at a lower precedence.
- **Item 9:** Precedence and Scoring System — Implement intelligent precedence rules for selecting the best matching service when multiple registrations could satisfy a request, with scoring that considers both context and location matches, and system vs site registration priority.

## Requirements Discussion

### First Round Questions

**Q1:** I assume the location-based service resolution will use Python's `pathlib.PurePath` for representing locations, following the roadmap's mention of "PurePath". Should we support both string and PurePath inputs in the registration API for developer convenience, or stick strictly to PurePath?

**Answer:** Actually, the Location system will use a custom Location class that is a tree-like data structure. It will support string inputs in the registration API for developer convenience, but internally maintain the tree structure.

**Q2:** For the precedence/scoring system, I'm thinking we should prioritize matches in this order: (1) exact context match, (2) exact location match, (3) system vs site registration. Should we make the scoring weights configurable, or hard-code these values for predictable behavior?

**Answer:** This needs clarification in follow-up questions.

**Q3:** The roadmap mentions "combining location with request selection but at a lower precedence." I assume this means if a service is registered with both a context predicate AND a location, it should score higher than one with just location alone. Is that the intended behavior?

**Answer:** Yes, that is correct. Both predicates contribute to the overall score, with combined matches scoring higher than single-predicate matches.

**Q4:** For location matching, should we support: (1) exact path matches only, (2) prefix matching (e.g., service at `/admin` matches request to `/admin/users`), or (3) hierarchical matching with most-specific-wins? I'm assuming option 3 is most useful, but want to confirm.

**Answer:** This needs clarification in follow-up questions.

**Q5:** When a request comes in with a location, where does that location parameter come from? Should it be: (1) explicitly passed to container.get(), (2) set on the container at creation time, or (3) available as a special service like "Location" that the container has access to?

**Answer:** This needs clarification in follow-up questions.

**Q6:** Looking at the existing HopscotchInjector code, I see it uses a flat list of ResourceInfo objects and iterates through them for every lookup. For location-based resolution, should we optimize this with a data structure like a tree or prefix map, or keep the simple iteration approach initially and optimize later?

**Answer:** This needs clarification in follow-up questions.

**Q7:** For the decorator/registration API, should `@injectable(location="/admin")` mean: (1) the decorated class is available ONLY when requested from that location, (2) it's PREFERRED at that location but still available elsewhere, or (3) we support both modes with different decorators/parameters?

**Answer:** This needs clarification in follow-up questions.

**Q8:** Are there any aspects of location-based resolution or precedence that are explicitly OUT OF SCOPE for this spec? For example: wildcard patterns in locations, regex matching, dynamic location computation, or custom scoring functions?

**Answer:** Yes, these are out of scope:
- Wildcard patterns in locations
- Regex matching
- Dynamic location computation
- Custom scoring functions

The focus is on simple, predictable location hierarchies and fixed precedence rules.

### Existing Code to Reference

**Similar Features Identified:**
- Feature: HopscotchInjector - Path: `src/svcs_di/injectors/hopscotch.py`
- Components: This already implements context-specific service resolution with predicate matching
- Backend logic: `ResourceInfo` dataclass stores factory, context predicates, and performs predicate-based matching
- Selection logic: `_select_resource` method iterates through registrations and calls `is_selected` to find matches

**Key Code Patterns to Follow:**
- The `ResourceInfo` dataclass pattern for storing registration metadata
- The `is_selected` method pattern for predicate checking
- The `_select_resource` method pattern for finding the best match
- The flat list iteration approach (though this may be optimized with new data structures)

**Integration Points:**
- This feature extends HopscotchInjector with location-based predicates
- Location matching will work alongside existing context predicates
- Precedence system will need to score both context and location matches

### Follow-up Questions

**Follow-up 1:** For the precedence/scoring system, should we make the scoring weights configurable, or hard-code these values for predictable behavior? Hard-coded would be simpler and more predictable, but configurable would be more flexible.

**Answer:** Hard coded values for predictable behavior.

**Follow-up 2:** You mentioned the Location system will be a tree-like data structure. Should the location matching walk up the tree hierarchy checking for exact matches at each level (most specific first), or should it use a different matching strategy?

**Answer:** Yes, most specific first (walk up the hierarchy checking exact matches at each level).

**Follow-up 3:** Where does the location parameter come from when making a request? Should it be: (1) explicitly passed to container.get(), (2) set on the container at creation time, or (3) available as a special service like "Location" that the container has access to?

**Answer:** Choice 3 - `Location` is a special service. When a container is made, it will have a `Location` put into it.

**Follow-up 4:** You mentioned that the HopscotchInjector's flat list iteration might be inefficient for location-based resolution. Should we optimize with a tree-based data structure (matching the Location tree), a ChainMap-like layered approach, or something else?

**Answer:** Possibly a tree or ChainMap or something else (open to efficient data structure choices).

**Follow-up 5:** For the decorator/registration API, should `@injectable(location="/admin")` mean the decorated class is available ONLY when requested from that location (not available elsewhere), or is it PREFERRED at that location but still available elsewhere?

**Answer:** Only - the decorated class is available ONLY when requested from that location or its children.

## Visual Assets

### Files Provided:
No visual files found in the visuals directory.

### Visual Insights:
No visual assets provided.

## Requirements Summary

### Functional Requirements

**Location System:**
- Implement a custom `Location` class as a tree-like data structure
- Location represents hierarchical paths (similar to URL paths or filesystem paths)
- Support string inputs in registration API that get converted to Location tree nodes
- Location matching walks up the hierarchy checking for exact matches at each level
- Most specific location match wins (deepest matching node in the tree)

**Service Registration with Location:**
- Extend registration API to accept a location parameter (string or Location)
- Services registered with a location are ONLY available when requested from that location or its children
- Services can be registered with both context predicates AND location predicates
- Internally, registrations store location information alongside existing context predicates

**Location as Special Service:**
- `Location` is a special service type that the container has access to
- When a container is created, it has a `Location` put into it
- This Location represents the current request's location context
- Services can depend on Location to access the current location

**Precedence and Scoring:**
- Hard-coded scoring weights for predictable behavior
- Scoring considers both context matches and location matches
- Services with both context AND location matches score higher than single-predicate matches
- When multiple services match, the highest score wins
- Scoring priority: exact context match + exact location match > context only > location only

**Location Matching Hierarchy:**
- Walk up the location tree from most specific to least specific
- Check for exact matches at each level
- First exact match found wins for that location level
- More specific matches (deeper in tree) take precedence over less specific matches

**Data Structure:**
- Open to efficient data structure choices (tree, ChainMap, or other)
- Must support efficient lookup by location in the tree hierarchy
- Should avoid iterating through all registrations for every lookup if possible
- Consider optimizations that preserve the flat list fallback for non-location queries

### Reusability Opportunities

**Existing Patterns to Extend:**
- `HopscotchInjector` in `src/svcs_di/injectors/hopscotch.py` - base for location features
- `ResourceInfo` dataclass pattern - extend to include location predicates
- `is_selected` method pattern - add location predicate checking
- `_select_resource` method - enhance with location hierarchy matching and scoring
- Existing context predicate system - location predicates should work alongside context predicates

**Components to Reference:**
- The predicate matching system for context-based selection
- The factory and metadata storage patterns in ResourceInfo
- The registration API patterns in HopscotchInjector

**New Components Needed:**
- `Location` class with tree-like data structure
- Location predicate for matching location hierarchies
- Scoring system that weighs both context and location matches
- Possibly a new data structure for efficient location-based lookups (tree or ChainMap)

### Scope Boundaries

**In Scope:**
- Custom Location class as a tree-like data structure
- Location-based service registration with string or Location inputs
- Location as a special service available in containers
- Hierarchical location matching (walk up tree, most specific first)
- Precedence/scoring system with hard-coded weights
- Combining context predicates with location predicates
- Services restricted to specific locations (ONLY available at that location or children)
- Efficient data structure for location-based lookups (tree, ChainMap, or other)
- Integration with existing HopscotchInjector patterns

**Out of Scope:**
- Wildcard patterns in locations (e.g., `/admin/*`)
- Regex matching for locations
- Dynamic location computation at runtime
- Custom scoring functions or configurable weights
- Services that are PREFERRED at a location but available elsewhere (only ONLY mode supported)
- Complex query languages for location matching
- Location-based access control or permissions
- Caching or performance optimizations beyond data structure choice

### Technical Considerations

**Design Decisions:**
- Location is a special service type (like context), not a parameter to container.get()
- Hard-coded scoring weights for predictability
- Exact match strategy walking up hierarchy (not prefix matching or glob patterns)
- ONLY mode for location-based registration (services not available outside their location)
- Both context and location predicates contribute to overall score

**Integration Points:**
- Extends HopscotchInjector with location capabilities
- Works alongside existing context-based predicates
- Location is set on container at creation time
- ResourceInfo or similar structure needs to store location predicates

**Data Structure Options:**
- Tree structure matching the Location tree hierarchy
- ChainMap for layered lookups by location level
- Other efficient structures for hierarchical lookup
- Must avoid flat list iteration overhead if possible

**Constraints from Tech Stack:**
- Python 3.14+ with type hints and protocols
- Must be compatible with free-threaded Python (PEP 703)
- Build on svcs Registry and Container abstractions
- Follow existing patterns in HopscotchInjector

**Similar Code Patterns:**
- HopscotchInjector's ResourceInfo and predicate matching
- Existing context-based service resolution
- Factory registration and retrieval patterns
- Decorator-based registration API (@injectable)
