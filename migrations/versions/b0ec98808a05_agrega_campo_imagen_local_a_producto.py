from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'b0ec98808a05'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c['name'] for c in insp.get_columns('producto')}

    with op.batch_alter_table('producto', schema=None) as batch_op:
        # Agregar imagen_local si no existe
        if 'imagen_local' not in cols:
            batch_op.add_column(sa.Column('imagen_local', sa.String(length=255), nullable=True))

        # Borrar imagen_url SOLO si existe
        if 'imagen_url' in cols:
            batch_op.drop_column('imagen_url')


def downgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c['name'] for c in insp.get_columns('producto')}

    with op.batch_alter_table('producto', schema=None) as batch_op:
        # Volver a crear imagen_url SOLO si no existe
        if 'imagen_url' not in cols:
            batch_op.add_column(sa.Column('imagen_url', sa.String(length=255), nullable=True))

        # Quitar imagen_local SOLO si existe
        if 'imagen_local' in cols:
            batch_op.drop_column('imagen_local')
