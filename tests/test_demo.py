"""데모 프로젝트 생성 및 전체 워크플로우 검증."""

import json
from pathlib import Path

import fitz

from src.capture import capture_file, capture_pdf, capture_text
from src.md_generator import generate_context_md
from src.project_manager import ProjectManager


def _create_sample_pdf(path: Path, title: str, pages: list[str]) -> Path:
    """테스트용 PDF 파일 생성."""
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


class TestDemoProject:
    """데모 프로젝트 생성 및 context.md 품질 검증."""

    def test_vbscript_migration_project(self, tmp_path):
        """VBScript 마이그레이션 프로젝트 데모."""
        pm = ProjectManager(data_dir=tmp_path)
        project = pm.create(
            "VBScript-Migration",
            description="VBScript에서 Python으로의 마이그레이션 프로젝트. "
            "기존 VBS 자동화 스크립트를 Python으로 전환하는 작업.",
        )

        captures_dir = tmp_path / "VBScript-Migration" / "captures"
        notes_dir = tmp_path / "VBScript-Migration" / "notes"

        # 1. 기존 VBS 코드 분석 메모
        capture_text(
            notes_dir,
            "VBScript Deprecation Analysis\n"
            "=============================\n\n"
            "Current State:\n"
            "- 47 VBS files in production\n"
            "- 12 are critical automation scripts\n"
            "- 8 interact with SAP via COM objects\n"
            "- 15 are simple file manipulation scripts\n\n"
            "Migration Priority:\n"
            "1. SAP COM scripts (highest risk)\n"
            "2. File automation scripts\n"
            "3. Report generation scripts\n\n"
            "Timeline: Q2 2026 completion target",
            description="VBS Deprecation 분석 보고서",
        )

        # 2. PDF 보고서
        _create_sample_pdf(
            tmp_path / "deprecation_report.pdf",
            "VBScript Deprecation Report",
            [
                "VBScript Deprecation Report\n\n"
                "Executive Summary\n"
                "Microsoft has officially deprecated VBScript.\n"
                "All scripts must be migrated by Q2 2026.\n\n"
                "Impact Assessment:\n"
                "- Production scripts: 47\n"
                "- Test scripts: 23\n"
                "- Estimated effort: 320 person-hours",
                "Migration Strategy\n\n"
                "Phase 1: Inventory and Assessment\n"
                "- Catalog all VBS scripts\n"
                "- Classify by complexity and risk\n"
                "- Identify dependencies\n\n"
                "Phase 2: Migration Execution\n"
                "- Convert simple scripts first\n"
                "- SAP COM scripts require special handling\n"
                "- Parallel testing with existing VBS",
                "Testing Plan\n\n"
                "- Unit tests for each migrated script\n"
                "- Integration tests with SAP\n"
                "- UAT with business users\n"
                "- 2-week parallel run before cutover",
            ],
        )
        capture_pdf(
            captures_dir, notes_dir,
            tmp_path / "deprecation_report.pdf",
            description="VBScript Deprecation Report",
        )

        # 3. 엑셀 파일 (가상)
        sample_xlsx = tmp_path / "migration_plan.xlsx"
        sample_xlsx.write_bytes(b"fake xlsx data")
        capture_file(captures_dir, sample_xlsx, description="마이그레이션 계획 엑셀")

        # 4. 고객 미팅 노트
        capture_text(
            notes_dir,
            "Customer Meeting Notes - 2026-04-01\n"
            "====================================\n\n"
            "Attendees: PM Kim, Dev Lee, Customer SDI team\n\n"
            "Key Points:\n"
            "- Customer wants Python + PowerShell hybrid approach\n"
            "- SAP scripts must maintain COM compatibility\n"
            "- Deadline: June 30, 2026 (hard deadline)\n"
            "- Budget approved for 2 additional developers\n\n"
            "Action Items:\n"
            "- [ ] Send migration plan by April 5\n"
            "- [ ] Setup Python dev environment on customer servers\n"
            "- [ ] Schedule weekly sync meetings",
            description="고객 미팅 노트 (SDI)",
        )

        # 5. 코드 스니펫 메모
        capture_text(
            notes_dir,
            "# VBS to Python conversion example\n\n"
            "## Before (VBS):\n"
            "```vbs\n"
            "Set objFSO = CreateObject(\"Scripting.FileSystemObject\")\n"
            "Set objFile = objFSO.OpenTextFile(\"data.csv\", 1)\n"
            "Do Until objFile.AtEndOfStream\n"
            "    strLine = objFile.ReadLine\n"
            "    WScript.Echo strLine\n"
            "Loop\n"
            "```\n\n"
            "## After (Python):\n"
            "```python\n"
            "with open('data.csv', 'r') as f:\n"
            "    for line in f:\n"
            "        print(line.strip())\n"
            "```",
            description="VBS→Python 변환 예시 코드",
        )

        # context.md 생성
        context_path = generate_context_md(
            "VBScript-Migration",
            tmp_path / "VBScript-Migration",
            description=project.description,
            created_at=project.created_at,
        )

        # --- 품질 검증 ---
        content = context_path.read_text(encoding="utf-8")

        # 기본 구조 확인
        assert "# 프로젝트: VBScript-Migration" in content
        assert "## 개요" in content
        assert "## 타임라인" in content

        # 캡처 수 확인 (텍스트3 + PDF파일1 + PDF추출1 + 엑셀파일1 = 6)
        assert "캡처 수: 6건" in content

        # PDF 추출 내용 포함 확인
        assert "## 문서 내용 (PDF 추출)" in content
        assert "VBScript Deprecation Report" in content
        assert "Migration Strategy" in content

        # 텍스트 노트 포함 확인
        assert "## 텍스트 노트" in content
        assert "VBS Deprecation 분석 보고서" in content
        assert "47 VBS files" in content
        assert "고객 미팅 노트" in content
        assert "June 30, 2026" in content

        # 파일 목록 확인
        assert "## 파일 목록" in content
        assert "migration_plan.xlsx" in content

        # context.md가 AI에게 유용한 수준인지 확인
        # 최소 500자 이상 (충분한 맥락)
        assert len(content) > 500, f"context.md가 너무 짧음: {len(content)}자"

        # 섹션이 올바른 순서인지 확인
        overview_pos = content.index("## 개요")
        timeline_pos = content.index("## 타임라인")
        pdf_pos = content.index("## 문서 내용")
        notes_pos = content.index("## 텍스트 노트")
        files_pos = content.index("## 파일 목록")
        assert overview_pos < timeline_pos < pdf_pos < notes_pos < files_pos

    def test_edm_collaboration_project(self, tmp_path):
        """EDM Collaboration 프로젝트 데모."""
        pm = ProjectManager(data_dir=tmp_path)
        project = pm.create(
            "EDM-Collaboration",
            description="EDM(Engineering Data Management) Collaborator 도구 "
            "도입 프로젝트. 고객사 엔지니어링 데이터 관리 시스템 구축.",
        )

        captures_dir = tmp_path / "EDM-Collaboration" / "captures"
        notes_dir = tmp_path / "EDM-Collaboration" / "notes"

        # 1. 제품 개요 PDF
        _create_sample_pdf(
            tmp_path / "edm_overview.pdf",
            "EDM Collaboration Overview",
            [
                "EDM Collaboration Overview (VX.2.11)\n\n"
                "Product Features:\n"
                "- Real-time collaboration on engineering data\n"
                "- Version control for CAD files\n"
                "- BOM management integration\n"
                "- Change order workflow automation\n\n"
                "System Requirements:\n"
                "- Windows 10/11 64-bit\n"
                "- 16GB RAM minimum\n"
                "- SQL Server 2019+",
                "Admin Guide\n\n"
                "Installation Steps:\n"
                "1. Run HIGHSPEED installer\n"
                "2. Configure database connection\n"
                "3. Setup user permissions\n"
                "4. Import initial data\n\n"
                "Configuration:\n"
                "- Server: edm.internal.corp\n"
                "- Port: 8443\n"
                "- Auth: LDAP integration",
            ],
        )
        capture_pdf(
            captures_dir, notes_dir,
            tmp_path / "edm_overview.pdf",
            description="EDM Collaboration Overview",
        )

        # 2. 기술 메모
        capture_text(
            notes_dir,
            "EDM Collaborator Setup Notes\n"
            "============================\n\n"
            "Environment: Customer production server\n"
            "DB: SQL Server 2022\n"
            "Users: 150 engineers across 3 sites\n\n"
            "Issues Found:\n"
            "- License server timeout after 4 hours idle\n"
            "- CAD file sync delay > 30 seconds for large assemblies\n"
            "- BOM export format not compatible with customer ERP\n\n"
            "Resolution:\n"
            "- Increase license timeout to 8 hours\n"
            "- Enable incremental sync for assemblies > 500MB\n"
            "- Custom BOM export template for SAP integration",
            description="EDM 셋업 이슈 및 해결",
        )

        # context.md 생성
        context_path = generate_context_md(
            "EDM-Collaboration",
            tmp_path / "EDM-Collaboration",
            description=project.description,
            created_at=project.created_at,
        )

        content = context_path.read_text(encoding="utf-8")

        # 품질 검증
        assert "EDM-Collaboration" in content
        assert "## 문서 내용 (PDF 추출)" in content
        assert "Real-time collaboration" in content
        assert "EDM 셋업 이슈 및 해결" in content
        assert "License server timeout" in content
        assert len(content) > 300

    def test_context_md_completeness_score(self, tmp_path):
        """context.md 완성도 점수 측정."""
        pm = ProjectManager(data_dir=tmp_path)
        pm.create("score-test", description="완성도 테스트")

        captures_dir = tmp_path / "score-test" / "captures"
        notes_dir = tmp_path / "score-test" / "notes"

        # 다양한 타입의 데이터 추가
        capture_text(notes_dir, "Meeting notes content", description="회의록")

        _create_sample_pdf(tmp_path / "doc.pdf", "Document", ["Page 1 content"])
        capture_pdf(captures_dir, notes_dir, tmp_path / "doc.pdf", description="문서")

        sample = tmp_path / "data.xlsx"
        sample.write_bytes(b"data")
        capture_file(captures_dir, sample, description="데이터")

        context_path = generate_context_md(
            "score-test", tmp_path / "score-test",
            description="완성도 테스트", created_at="2026-04-01T09:00:00",
        )
        content = context_path.read_text(encoding="utf-8")

        # 점수 매기기
        score = 0
        checks = [
            ("프로젝트 제목", "# 프로젝트: score-test" in content),
            ("설명", "완성도 테스트" in content),
            ("생성일", "2026-04-01" in content),
            ("마지막 업데이트", "마지막 업데이트" in content),
            ("캡처 수", "캡처 수:" in content),
            ("타임라인 섹션", "## 타임라인" in content),
            ("PDF 추출 섹션", "## 문서 내용" in content),
            ("텍스트 노트 섹션", "## 텍스트 노트" in content),
            ("파일 목록 섹션", "## 파일 목록" in content),
            ("PDF 내용 포함", "Page 1 content" in content),
            ("노트 내용 포함", "Meeting notes content" in content),
            ("파일명 포함", "data.xlsx" in content),
        ]

        for name, passed in checks:
            if passed:
                score += 1

        total = len(checks)
        percentage = (score / total) * 100

        assert percentage >= 90, (
            f"완성도 {percentage:.0f}% ({score}/{total}) - "
            f"실패: {[n for n, p in checks if not p]}"
        )
