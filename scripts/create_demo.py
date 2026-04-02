"""데모 프로젝트 생성 스크립트."""

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.project_manager import ProjectManager
from src.capture import capture_pdf, capture_file, capture_text
from src.md_generator import generate_context_md

DATA_DIR = Path(__file__).parent.parent / "data"


def main():
    pm = ProjectManager(data_dir=DATA_DIR)

    name = "VBScript-Migration"
    if not pm.exists(name):
        pm.create(name, description=(
            "VBScript to Python migration project. "
            "Converting legacy VBS automation scripts to Python."
        ))

    captures_dir = DATA_DIR / name / "captures"
    notes_dir = DATA_DIR / name / "notes"

    dl = Path.home() / "Downloads"

    # PDF files
    for pdf_name in [
        "EDM Collaboration Overview (VX.2.11).pdf",
        "EDM_Collaborator_for_admin_v0.3.pdf",
    ]:
        pdf_path = dl / pdf_name
        if pdf_path.exists():
            capture_pdf(captures_dir, notes_dir, pdf_path, description=pdf_name.replace(".pdf", ""))
            print(f"PDF added: {pdf_name}")

    # PPTX file
    pptx_path = dl / "CY26-03 EBS Korea Monthly Sync_20260320.pptx"
    if pptx_path.exists():
        capture_file(captures_dir, pptx_path, description="EBS Korea Monthly Sync")
        print(f"File added: {pptx_path.name}")

    # XLSX file
    xlsx_path = dl / "부품특성추출결과_2602.xlsx"
    if xlsx_path.exists():
        capture_file(captures_dir, xlsx_path, description="Component analysis results")
        print("File added: xlsx")

    # Text memos
    capture_text(
        notes_dir,
        "VBScript Deprecation Status\n"
        "===========================\n\n"
        "Total VBS files: 47\n"
        "Migration complete: 12\n"
        "In progress: 8\n"
        "Not started: 27\n\n"
        "Priority:\n"
        "1. SAP COM scripts (8) - high risk\n"
        "2. File automation scripts (15)\n"
        "3. Report generation scripts (24)\n\n"
        "Deadline: June 30, 2026\n"
        "Team: Dev Lee, PM Kim",
        description="VBScript migration status summary",
    )
    print("Text added: migration status")

    capture_text(
        notes_dir,
        "Customer Meeting Notes - Samsung SDI\n"
        "=====================================\n\n"
        "Date: 2026-03-20\n"
        "Attendees: PM Kim, Dev Lee, Customer SDI team\n\n"
        "Key Discussion:\n"
        "- Agreed on Python + PowerShell hybrid approach\n"
        "- SAP scripts must maintain COM compatibility\n"
        "- Hard deadline: June 30, 2026\n"
        "- 2 additional developers approved\n\n"
        "Action Items:\n"
        "- Send migration plan by April 5\n"
        "- Setup Python env on customer servers\n"
        "- Schedule weekly sync meetings",
        description="Samsung SDI customer meeting notes",
    )
    print("Text added: customer meeting notes")

    capture_text(
        notes_dir,
        "# VBS to Python Conversion Examples\n\n"
        "## File Reading\n"
        "### Before (VBS):\n"
        "```vbs\n"
        'Set objFSO = CreateObject("Scripting.FileSystemObject")\n'
        'Set objFile = objFSO.OpenTextFile("data.csv", 1)\n'
        "Do Until objFile.AtEndOfStream\n"
        "    strLine = objFile.ReadLine\n"
        "    WScript.Echo strLine\n"
        "Loop\n"
        "```\n\n"
        "### After (Python):\n"
        "```python\n"
        "with open('data.csv', 'r') as f:\n"
        "    for line in f:\n"
        "        print(line.strip())\n"
        "```\n\n"
        "## SAP COM Interaction\n"
        "### Before (VBS):\n"
        "```vbs\n"
        'Set SapGui = GetObject("SAPGUI")\n'
        "Set App = SapGui.GetScriptingEngine\n"
        "Set Connection = App.Children(0)\n"
        "Set Session = Connection.Children(0)\n"
        "```\n\n"
        "### After (Python):\n"
        "```python\n"
        "import win32com.client\n"
        "sap_gui = win32com.client.GetObject('SAPGUI')\n"
        "app = sap_gui.GetScriptingEngine\n"
        "connection = app.Children(0)\n"
        "session = connection.Children(0)\n"
        "```",
        description="VBS to Python conversion examples",
    )
    print("Text added: conversion examples")

    # Generate context.md
    project = pm.get(name)
    ctx = generate_context_md(
        name, DATA_DIR / name,
        description=project.description,
        created_at=project.created_at,
    )
    print(f"\ncontext.md generated: {ctx}")
    print(f"File size: {ctx.stat().st_size} bytes")


if __name__ == "__main__":
    main()
