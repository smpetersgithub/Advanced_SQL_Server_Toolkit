"""
Script to classify functional dependencies by relevance.
Identifies redundant, minimal, and key dependencies.
Updates the JSON results with relevance classifications.
"""

import json
import sys
from datetime import datetime
from config_loader import ConfigLoader


def load_results(results_path):
    """
    Load the functional dependency analysis results from JSON file.

    Args:
        results_path: Path to the JSON results file

    Returns:
        Dictionary containing the analysis results

    Raises:
        FileNotFoundError: If results file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        with open(results_path, 'r') as f:
            results = json.load(f)
        print(f"Results loaded from: {results_path}")
        return results
    except FileNotFoundError:
        print(f"Error: Results file not found at {results_path}")
        print("Please run the 'Analyze Functional Dependencies' script first.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in results file: {e}")
        sys.exit(1)


def normalize_determinant(determinant):
    """Normalize determinant to a set for comparison."""
    if isinstance(determinant, list):
        return frozenset(determinant)
    return frozenset([determinant])


def is_subset_determinant(det_a, det_b):
    """
    Check if det_a is a proper subset of det_b.
    Returns True if det_a ⊂ det_b (det_a is smaller and contained in det_b)
    """
    set_a = normalize_determinant(det_a)
    set_b = normalize_determinant(det_b)
    return set_a < set_b  # Proper subset (not equal)


def validate_results_structure(results):
    """
    Validate that the results dictionary has the expected structure.

    Args:
        results: Dictionary loaded from JSON file

    Raises:
        ValueError: If required fields are missing or invalid
    """
    if not isinstance(results, dict):
        raise ValueError("Results must be a dictionary")

    # Check for required fields
    if 'functional_dependencies' not in results:
        raise ValueError("Results missing 'functional_dependencies' field")

    fd_list = results.get('functional_dependencies')
    if not isinstance(fd_list, list):
        raise ValueError("'functional_dependencies' must be a list")

    if len(fd_list) == 0:
        raise ValueError("No functional dependencies found to classify. Please run the analysis script first.")


def classify_functional_dependencies(results):
    """
    Classify functional dependencies by relevance.

    Classifications:
    - MINIMAL: The smallest determinant for this dependent (most relevant)
    - REDUNDANT: A larger determinant that includes a minimal one (less relevant)
    - PARTIAL_DEPENDENCY: Violates 2NF - non-prime attribute depends on part of composite PK
    - CANDIDATE_KEY: Determinant is the primary key or unique key
    - TRIVIAL: Determinant contains the dependent (always true, not useful)

    Args:
        results: Dictionary containing analysis results

    Returns:
        List of classified functional dependencies
    """
    fd_list = results.get('functional_dependencies', [])
    primary_key = results.get('primarykey', '')
    unique_keys = results.get('uniquekey', [])

    # Normalize primary key
    if isinstance(primary_key, str):
        pk_set = frozenset([primary_key]) if primary_key else frozenset()
    else:
        pk_set = frozenset(primary_key) if primary_key else frozenset()

    # Normalize unique keys
    uk_sets = []
    if unique_keys:
        for uk in unique_keys:
            if isinstance(uk, list):
                uk_sets.append(frozenset(uk))
            else:
                uk_sets.append(frozenset([uk]))

    # Group FDs by dependent column
    deps_by_dependent = {}
    for fd in fd_list:
        dependent = fd.get('dependent')
        if dependent not in deps_by_dependent:
            deps_by_dependent[dependent] = []
        deps_by_dependent[dependent].append(fd)

    # Classify each FD
    classified_fds = []

    for dependent, fds in deps_by_dependent.items():
        # Sort by determinant size (smallest first)
        fds_sorted = sorted(fds, key=lambda x: len(normalize_determinant(x.get('determinant'))))

        # First pass: identify trivial dependencies and tag key types
        non_trivial_fds = []
        for fd in fds_sorted:
            det = fd.get('determinant')
            det_set = normalize_determinant(det)

            # Check if this determinant contains the dependent (trivial)
            if dependent in det_set:
                fd['relevance'] = 'TRIVIAL'
                fd['relevance_reason'] = f'Determinant contains dependent ({dependent})'
                classified_fds.append(fd)
                continue

            # Tag if determinant is primary key or unique key (but don't classify yet)
            fd['_is_primary_key'] = (det_set == pk_set)
            fd['_is_unique_key'] = (det_set in uk_sets)

            # Add to non-trivial list for minimal/redundant classification
            non_trivial_fds.append(fd)

        # Second pass: find truly minimal determinants
        # A determinant is minimal if no other determinant is a proper subset of it
        for i, fd in enumerate(non_trivial_fds):
            det_set = normalize_determinant(fd.get('determinant'))
            is_minimal = True
            minimal_subset = None

            # Check if any OTHER determinant is a proper subset of this one
            for j, other_fd in enumerate(non_trivial_fds):
                if i == j:
                    continue
                other_det_set = normalize_determinant(other_fd.get('determinant'))

                # If other_det_set is a proper subset of det_set, then det_set is redundant
                if other_det_set < det_set:  # Proper subset
                    is_minimal = False
                    minimal_subset = other_det_set
                    break

            # Now classify based on minimal/redundant AND key status
            if is_minimal:
                # Check if this is a primary key or unique key
                if fd.get('_is_primary_key'):
                    fd['relevance'] = 'PRIMARY_KEY'
                    fd['relevance_reason'] = 'Determinant is the primary key'
                elif fd.get('_is_unique_key'):
                    fd['relevance'] = 'UNIQUE_KEY'
                    fd['relevance_reason'] = 'Determinant is a unique key'
                else:
                    # Check for PARTIAL DEPENDENCY (2NF violation)
                    # This occurs when:
                    # 1. Primary key is composite (has multiple columns)
                    # 2. This determinant is a proper subset of the primary key
                    # 3. The dependent is NOT part of any key (non-prime attribute)
                    is_partial_dependency = False
                    if len(pk_set) > 1 and det_set < pk_set:
                        # Determinant is a proper subset of composite primary key
                        # Check if dependent is a non-prime attribute (not part of any key)
                        is_prime_attribute = dependent in pk_set
                        for uk_set in uk_sets:
                            if dependent in uk_set:
                                is_prime_attribute = True
                                break

                        if not is_prime_attribute:
                            is_partial_dependency = True

                    if is_partial_dependency:
                        fd['relevance'] = 'PARTIAL_DEPENDENCY'
                        pk_str = ', '.join(sorted(pk_set))
                        det_str = ', '.join(sorted(det_set)) if len(det_set) > 1 else list(det_set)[0]
                        fd['relevance_reason'] = f'2NF VIOLATION: Non-prime attribute depends on part of composite PK [{pk_str}]'
                    else:
                        fd['relevance'] = 'MINIMAL'
                        fd['relevance_reason'] = 'Smallest determinant for this dependent'
            else:
                minimal_det_str = ', '.join(sorted(minimal_subset)) if len(minimal_subset) > 1 else list(minimal_subset)[0]
                fd['relevance'] = 'REDUNDANT'
                fd['relevance_reason'] = f'Superset of minimal determinant: [{minimal_det_str}]'

            # Clean up temporary flags
            fd.pop('_is_primary_key', None)
            fd.pop('_is_unique_key', None)

            classified_fds.append(fd)

    return classified_fds


def update_results_with_classification(results):
    """Update the results with relevance classifications."""
    print("\n" + "=" * 80)
    print("Classifying Functional Dependencies by Relevance")
    print("=" * 80)
    
    # Classify FDs
    classified_fds = classify_functional_dependencies(results)
    
    # Count by relevance
    relevance_counts = {}
    for fd in classified_fds:
        relevance = fd.get('relevance', 'UNKNOWN')
        relevance_counts[relevance] = relevance_counts.get(relevance, 0) + 1
    
    # Update results
    results['functional_dependencies'] = classified_fds
    
    # Update categorized lists
    results['single_column_dependencies'] = [
        fd for fd in classified_fds 
        if fd.get('determinant_size', 1) == 1
    ]
    results['composite_dependencies'] = [
        fd for fd in classified_fds 
        if fd.get('determinant_size', 1) > 1
    ]
    
    # Add relevance summary
    results['relevance_summary'] = relevance_counts
    
    # Print summary
    print("\nRelevance Classification Summary:")
    print("-" * 80)
    for relevance, count in sorted(relevance_counts.items()):
        print(f"  {relevance}: {count}")
    print("-" * 80)
    
    return results


def save_results(results, output_path):
    """
    Save the updated results back to JSON file.

    Args:
        results: Dictionary containing classified results
        output_path: Path where to save the JSON file

    Raises:
        IOError: If file cannot be written
        PermissionError: If no permission to write file
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nUpdated results saved to: {output_path}")
    except PermissionError:
        print(f"Error: Permission denied writing to {output_path}")
        print("Please check file permissions and try again.")
        sys.exit(1)
    except IOError as e:
        print(f"Error: Cannot write to file {output_path}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error saving results file: {e}")
        sys.exit(1)


def main():
    """Main function to classify dependency relevance."""
    print("=" * 80)
    print("Functional Dependency Relevance Classifier")
    print("=" * 80)

    try:
        # Load configuration using ConfigLoader
        config_loader = ConfigLoader()
        results_path = config_loader.get_functional_dependencies_path()

        # Validate that results file path exists
        from pathlib import Path
        if not Path(results_path).exists():
            print(f"Error: Results file not found at {results_path}")
            print("Please run the 'Analyze Functional Dependencies' script first.")
            sys.exit(1)

        # Load results
        results = load_results(results_path)

        # Validate results structure
        validate_results_structure(results)

        # Classify and update
        results = update_results_with_classification(results)

        # Save updated results
        save_results(results, results_path)

        print("=" * 80)
        print("Classification completed successfully!")
        print("=" * 80)

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print("=" * 80)
        print(f"ERROR: Classification failed: {e}")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
