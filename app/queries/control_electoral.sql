--CONTROL ELECTORAL
SELECT
    DISTINCT rec.cod_recinto,
    rec.nom_recinto,
    (
        SELECT
            COUNT(*)
        FROM
            junta j
        WHERE
            j.cod_recinto = rec.cod_recinto
            AND j.muestra = 0
    ) AS delegados_asignar,
    (
        SELECT
            COUNT(*)
        FROM
            junta j
            JOIN formulario_control_electoral f
            ON j.cod_junta = f.cod_junta
            AND j.cod_recinto = rec.cod_recinto
            AND j.muestra = 0
    ) AS delegados_asignados
FROM
    recintos rec
    JOIN junta jun
    ON rec.cod_recinto = jun.cod_recinto
WHERE
    jun.muestra = 0;
