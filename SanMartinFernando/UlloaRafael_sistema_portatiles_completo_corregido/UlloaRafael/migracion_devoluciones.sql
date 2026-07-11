-- Ejecutar una sola vez en una instalación existente de sistemaportatiles.
-- Es seguro volver a ejecutarlo: utiliza comprobaciones IF NOT EXISTS.

ALTER TABLE prestamos
ADD COLUMN IF NOT EXISTS responsable_devolucion_id INT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_responsable_devolucion'
    ) THEN
        ALTER TABLE prestamos
        ADD CONSTRAINT fk_responsable_devolucion
        FOREIGN KEY (responsable_devolucion_id)
        REFERENCES usuarios(id)
        ON DELETE RESTRICT;
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_prestamos_responsable_devolucion
ON prestamos(responsable_devolucion_id);
