"""
Recursively extract all ICD-10-CM diagnoses from the tabular XML file.
This script extracts diagnoses at all levels of the hierarchy with their metadata.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any
import json


def clean_text(text: str) -> str:
    """Clean whitespace from text."""
    import re
    return re.sub(r"\s+", " ", text or "").strip()


def extract_notes(diag_elem: ET.Element, note_type: str) -> List[str]:
    """Extract notes of a specific type from a diagnosis element."""
    notes = []
    for note_elem in diag_elem.findall(f".//{note_type}"):
        for note in note_elem.findall(".//note"):
            if note.text:
                notes.append(clean_text(note.text))
    return notes


def extract_inclusion_terms(diag_elem: ET.Element) -> List[str]:
    """Extract inclusion terms from a diagnosis element."""
    terms = []
    for inclusion in diag_elem.findall(".//inclusionTerm"):
        for note in inclusion.findall(".//note"):
            if note.text:
                terms.append(clean_text(note.text))
    return terms


def extract_diagnosis_recursive(diag_elem: ET.Element, parent_code: str = None,
                                level: int = 0) -> List[Dict[str, Any]]:
    """
    Recursively extract a diagnosis and all its children.

    Args:
        diag_elem: The <diag> XML element
        parent_code: The code of the parent diagnosis
        level: Current depth level in the hierarchy

    Returns:
        List of diagnosis dictionaries with all metadata
    """
    diagnoses = []

    # Extract current diagnosis information
    code = clean_text(diag_elem.findtext(".//name"))
    desc = clean_text(diag_elem.findtext(".//desc"))

    if not code:
        # If no code, skip but still process children
        for child_diag in diag_elem.findall("./diag"):
            diagnoses.extend(extract_diagnosis_recursive(child_diag, parent_code, level))
        return diagnoses

    # Build the diagnosis record
    diagnosis = {
        "code": code,
        "description": desc,
        "parent_code": parent_code,
        "level": level,
        "has_children": False,  # Will update if children found
        "inclusion_terms": extract_inclusion_terms(diag_elem),
        "includes": extract_notes(diag_elem, "includes"),
        "excludes1": extract_notes(diag_elem, "excludes1"),
        "excludes2": extract_notes(diag_elem, "excludes2"),
        "code_first": extract_notes(diag_elem, "codeFirst"),
        "use_additional_code": extract_notes(diag_elem, "useAdditionalCode"),
        "code_also": extract_notes(diag_elem, "codeAlso"),
    }

    # Find direct child <diag> elements (not nested deeper)
    child_diags = diag_elem.findall("./diag")

    if child_diags:
        diagnosis["has_children"] = True
        diagnosis["num_children"] = len(child_diags)
        diagnosis["is_billable"] = False  # Parent codes are typically not billable
    else:
        diagnosis["num_children"] = 0
        diagnosis["is_billable"] = True  # Leaf codes are typically billable

    diagnoses.append(diagnosis)

    # Recursively process children
    for child_diag in child_diags:
        child_diagnoses = extract_diagnosis_recursive(child_diag, code, level + 1)
        diagnoses.extend(child_diagnoses)

    return diagnoses


def extract_all_diagnoses(xml_path: Path) -> List[Dict[str, Any]]:
    """
    Extract all diagnoses from the ICD-10-CM tabular XML file.

    Args:
        xml_path: Path to the icd10cm-tabular XML file

    Returns:
        List of all diagnoses with metadata
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    all_diagnoses = []

    # Iterate through chapters and sections
    for chapter in root.findall(".//chapter"):
        chapter_name = clean_text(chapter.findtext(".//name"))
        chapter_desc = clean_text(chapter.findtext(".//desc"))

        # Process all sections in the chapter
        for section in chapter.findall(".//section"):
            section_id = section.get("id", "")
            section_desc = clean_text(section.findtext(".//desc"))

            # Process all top-level diagnoses in the section
            for diag in section.findall("./diag"):
                diagnoses = extract_diagnosis_recursive(diag, parent_code=None, level=0)

                # Add chapter and section context to each diagnosis
                for diagnosis in diagnoses:
                    diagnosis["chapter"] = chapter_name
                    diagnosis["chapter_desc"] = chapter_desc
                    diagnosis["section_id"] = section_id
                    diagnosis["section_desc"] = section_desc

                all_diagnoses.extend(diagnoses)

    return all_diagnoses


def print_diagnosis_tree(diagnoses: List[Dict[str, Any]], max_display: int = 50):
    """Print diagnoses in a tree format."""
    print(f"\nTotal diagnoses extracted: {len(diagnoses)}\n")
    print("Sample diagnosis tree (first {}):\n".format(max_display))

    for i, diag in enumerate(diagnoses[:max_display]):
        indent = "  " * diag["level"]
        billable = "✓" if diag["is_billable"] else "○"
        children_info = f" ({diag['num_children']} children)" if diag["has_children"] else ""

        print(f"{indent}{billable} {diag['code']}: {diag['description']}{children_info}")

        # Show some metadata for leaf nodes
        if diag["is_billable"] and i < 20:
            if diag["inclusion_terms"]:
                print(f"{indent}   Includes: {', '.join(diag['inclusion_terms'][:2])}")


def main():
    # Path to the XML file
    data_dir = Path("../data/icd10cm-table-and-index-2026")
    xml_path = data_dir / "icd10cm-tabular-2026.xml"

    if not xml_path.exists():
        print(f"Error: File not found at {xml_path}")
        return

    print(f"Extracting diagnoses from {xml_path}...")
    diagnoses = extract_all_diagnoses(xml_path)

    # Print tree view
    print_diagnosis_tree(diagnoses, max_display=100)

    # Statistics
    print("\n" + "="*60)
    print("STATISTICS")
    print("="*60)
    print(f"Total diagnoses: {len(diagnoses)}")
    print(f"Billable codes: {sum(1 for d in diagnoses if d['is_billable'])}")
    print(f"Parent codes: {sum(1 for d in diagnoses if d['has_children'])}")
    print(f"Max depth: {max(d['level'] for d in diagnoses)}")

    # Level distribution
    from collections import Counter
    level_counts = Counter(d['level'] for d in diagnoses)
    print("\nDiagnoses by level:")
    for level in sorted(level_counts.keys()):
        print(f"  Level {level}: {level_counts[level]}")

    # Sample diagnoses with most children
    print("\nTop parent codes by number of children:")
    parents = [d for d in diagnoses if d['has_children']]
    parents.sort(key=lambda x: x['num_children'], reverse=True)
    for parent in parents[:10]:
        print(f"  {parent['code']}: {parent['description']} ({parent['num_children']} children)")

    # Save to JSON for further analysis
    output_path = data_dir / "diagnoses_recursive.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(diagnoses, f, indent=2, ensure_ascii=False)
    print(f"\nSaved all diagnoses to {output_path}")

    # Save a CSV version for easy viewing
    import csv
    csv_path = data_dir / "diagnoses_recursive.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["code", "description", "parent_code", "level", "is_billable",
                     "num_children", "chapter", "section_id"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(diagnoses)
    print(f"Saved CSV to {csv_path}")


if __name__ == "__main__":
    main()
