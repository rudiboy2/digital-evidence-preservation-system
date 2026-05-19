"""Tanzania 2026 compliance fields - warrant, device metadata, TDFL forensic report fields

Revision ID: tz2026_compliance
Revises: workflow_v2_001
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'tz2026_compliance'
down_revision = 'workflow_v2_001'
branch_labels = None
depends_on = None


def upgrade():
    # ── Case: Investigator legal authority fields ──────────────────────
    op.add_column('cases', sa.Column('warrant_number',              sa.String(100),  nullable=True))
    op.add_column('cases', sa.Column('warrant_issuing_court',       sa.String(255),  nullable=True))
    op.add_column('cases', sa.Column('warrant_issue_date',          sa.DateTime(),   nullable=True))
    op.add_column('cases', sa.Column('warrant_expiry_date',         sa.DateTime(),   nullable=True))
    op.add_column('cases', sa.Column('ob_number',                   sa.String(100),  nullable=True))
    op.add_column('cases', sa.Column('dpp_reference_number',        sa.String(100),  nullable=True))
    op.add_column('cases', sa.Column('court_name',                  sa.String(255),  nullable=True))
    op.add_column('cases', sa.Column('court_case_number',           sa.String(100),  nullable=True))
    op.add_column('cases', sa.Column('next_hearing_date',           sa.DateTime(),   nullable=True))
    op.add_column('cases', sa.Column('court_status',                sa.String(50),   nullable=True))
    op.add_column('cases', sa.Column('referring_agency',            sa.String(100),  nullable=True))
    op.add_column('cases', sa.Column('external_reference',          sa.String(100),  nullable=True))
    op.add_column('cases', sa.Column('evidence_submitted_to_court', sa.Boolean(),    nullable=True, server_default='false'))
    op.add_column('cases', sa.Column('evidence_submitted_date',     sa.DateTime(),   nullable=True))

    # ── Evidence: Officer collection metadata (TPF-SOP-DE-2021) ───────
    op.add_column('evidence', sa.Column('evidence_source_type',  sa.String(50),  nullable=True))
    op.add_column('evidence', sa.Column('device_type',           sa.String(100), nullable=True))
    op.add_column('evidence', sa.Column('device_make',           sa.String(100), nullable=True))
    op.add_column('evidence', sa.Column('device_model',          sa.String(100), nullable=True))
    op.add_column('evidence', sa.Column('device_serial_number',  sa.String(100), nullable=True))
    op.add_column('evidence', sa.Column('device_imei',           sa.String(20),  nullable=True))
    op.add_column('evidence', sa.Column('collection_method',     sa.String(100), nullable=True))
    op.add_column('evidence', sa.Column('collection_location',   sa.String(500), nullable=True))
    op.add_column('evidence', sa.Column('collection_gps_lat',    sa.Float(),     nullable=True))
    op.add_column('evidence', sa.Column('collection_gps_lng',    sa.Float(),     nullable=True))
    op.add_column('evidence', sa.Column('collection_date',       sa.DateTime(),  nullable=True))
    op.add_column('evidence', sa.Column('witness_name',          sa.String(255), nullable=True))
    op.add_column('evidence', sa.Column('witness_badge_number',  sa.String(50),  nullable=True))
    op.add_column('evidence', sa.Column('physical_seal_number',  sa.String(100), nullable=True))
    op.add_column('evidence', sa.Column('evidence_bag_number',   sa.String(100), nullable=True))
    op.add_column('evidence', sa.Column('exhibit_tag_number',    sa.String(100), nullable=True))
    op.add_column('evidence', sa.Column('witness_statement_ref', sa.String(100), nullable=True))
    op.add_column('evidence', sa.Column('forensic_copy_hash',    sa.String(64),  nullable=True))

    # ── Analysis Reports: TDFL-STD-2023 mandatory fields ──────────────
    op.add_column('analysis_reports', sa.Column('analyst_certification_number',      sa.String(100), nullable=True))
    op.add_column('analysis_reports', sa.Column('forensic_tool_name',                sa.String(200), nullable=True))
    op.add_column('analysis_reports', sa.Column('forensic_tool_version',             sa.String(100), nullable=True))
    op.add_column('analysis_reports', sa.Column('lab_reference_number',              sa.String(100), nullable=True))
    op.add_column('analysis_reports', sa.Column('examination_start_date',            sa.DateTime(),  nullable=True))
    op.add_column('analysis_reports', sa.Column('examination_end_date',              sa.DateTime(),  nullable=True))
    op.add_column('analysis_reports', sa.Column('work_copy_hash',                    sa.String(64),  nullable=True))
    op.add_column('analysis_reports', sa.Column('independence_statement',            sa.Boolean(),   nullable=True, server_default='false'))
    op.add_column('analysis_reports', sa.Column('independence_statement_text',       sa.Text(),      nullable=True))
    op.add_column('analysis_reports', sa.Column('copies_made',                       sa.Integer(),   nullable=True))
    op.add_column('analysis_reports', sa.Column('copies_location',                   sa.Text(),      nullable=True))
    op.add_column('analysis_reports', sa.Column('is_expert_witness',                 sa.Boolean(),   nullable=True, server_default='false'))
    op.add_column('analysis_reports', sa.Column('expert_witness_court_designation',  sa.String(255), nullable=True))
    op.add_column('analysis_reports', sa.Column('analyst_declaration',               sa.Text(),      nullable=True))


def downgrade():
    for col in ['warrant_number','warrant_issuing_court','warrant_issue_date',
                'warrant_expiry_date','ob_number','dpp_reference_number','court_name',
                'court_case_number','next_hearing_date','court_status','referring_agency',
                'external_reference','evidence_submitted_to_court','evidence_submitted_date']:
        op.drop_column('cases', col)

    for col in ['evidence_source_type','device_type','device_make','device_model',
                'device_serial_number','device_imei','collection_method','collection_location',
                'collection_gps_lat','collection_gps_lng','collection_date','witness_name',
                'witness_badge_number','physical_seal_number','evidence_bag_number',
                'exhibit_tag_number','witness_statement_ref','forensic_copy_hash']:
        op.drop_column('evidence', col)

    for col in ['analyst_certification_number','forensic_tool_name','forensic_tool_version',
                'lab_reference_number','examination_start_date','examination_end_date',
                'work_copy_hash','independence_statement','independence_statement_text',
                'copies_made','copies_location','is_expert_witness',
                'expert_witness_court_designation','analyst_declaration']:
        op.drop_column('analysis_reports', col)
