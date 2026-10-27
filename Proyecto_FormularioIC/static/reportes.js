
let todosLosReportes = [];

async function abrirReportes() {
    const modal = document.getElementById("modal-reportes");

    if (!modal) {
        alert("No se encontró la ventana de reportes.");
        return;
    }

    try {
        const respuesta = await fetch("/reportes-analistas");

        if (!respuesta.ok) {
            throw new Error("No se pudieron consultar los reportes.");
        }

        todosLosReportes = await respuesta.json();

        const selectorMes = document.getElementById("reportes-mes");
        const selectorCanal = document.getElementById("reportes-canal");

        const meses = [...new Set(
            todosLosReportes.map(r => r.periodo)
        )].sort().reverse();

        selectorMes.innerHTML = meses.map(mes =>
            `<option value="${mes}">${formatearMes(mes)}</option>`
        ).join("");

        selectorCanal.innerHTML = '<option value="">Todos los canales</option>';

        selectorMes.onchange = () => {
            actualizarCanales();
            actualizarAnalistas();
            filtrarReportes();
        };

        selectorCanal.onchange = () => {
            actualizarAnalistas();
            filtrarReportes();
        };

        document.getElementById("reportes-analista").onchange = filtrarReportes;

        actualizarCanales();
        actualizarAnalistas();
        filtrarReportes();

        modal.hidden = false;

    } catch (error) {
        alert("Error al cargar los reportes: " + error.message);
    }
}

function cerrarReportes() {
    document.getElementById("modal-reportes").hidden = true;
}

function formatearMes(periodo) {
    const [anio, mes] = periodo.split("-");

    const fecha = new Date(Number(anio), Number(mes) - 1, 1);

    return fecha.toLocaleDateString("es-PE", {
        month: "long",
        year: "numeric"
    });
}

function actualizarCanales() {
    const periodo = document.getElementById("reportes-mes").value;
    const selector = document.getElementById("reportes-canal");

    const canales = [...new Set(
        todosLosReportes
            .filter(r => r.periodo === periodo)
            .map(r => (r.canal || "").trim().toUpperCase())
            .filter(Boolean)
    )].sort();

    selector.innerHTML = '<option value="">Todos los canales</option>';

    canales.forEach(canal => {
        selector.add(new Option(canal, canal));
    });
}

function actualizarAnalistas() {
    const periodo = document.getElementById("reportes-mes").value;
    const canal = document.getElementById("reportes-canal").value;
    const selector = document.getElementById("reportes-analista");

    const analistas = [...new Set(
        todosLosReportes
            .filter(r =>
                r.periodo === periodo &&
                (!canal || (r.canal || "").trim().toUpperCase() === canal)
            )
            .map(r => (r.analista || "").trim())
            .filter(Boolean)
    )].sort((a, b) => a.localeCompare(b, "es"));

    selector.replaceChildren();
    selector.add(new Option("Todos los analistas", ""));

    analistas.forEach(analista => {
        selector.add(new Option(analista, analista));
    });
}


function obtenerReportesFiltrados() {
    const periodo = document.getElementById("reportes-mes").value;
    const canal = document.getElementById("reportes-canal").value;
    const analista = document.getElementById("reportes-analista").value;

    return todosLosReportes.filter(r =>
        r.periodo === periodo &&
        (!canal || (r.canal || "").trim().toUpperCase() === canal) &&
        (!analista || (r.analista || "").trim() === analista)
    );
}


function filtrarReportes() {
    const tbody = document.getElementById("reportes-tbody");
    const registros = obtenerReportesFiltrados();

    tbody.replaceChildren();

    if (!registros.length) {
        const fila = tbody.insertRow();
        const celda = fila.insertCell();
        celda.colSpan = 4;
        celda.textContent = "No hay reportes para este periodo y canal.";
        return;
    }

    registros.forEach(r => {
        const fila = tbody.insertRow();

        [
            r.analista,
            r.reporte,
            r.kpi,
            r.frecuencia
        ].forEach(valor => {
            const celda = fila.insertCell();
            celda.textContent = valor || "";
        });
    });
}

function descargarReportes() {
    const registros = obtenerReportesFiltrados();

    if (!registros.length) {
        alert("No hay reportes para descargar.");
        return;
    }

    const filas = [
        ["Analista", "Nombre de Reporte", "KPI que revisan", "Frecuencia actualización"],
        ...registros.map(r => [
            r.analista, r.reporte, r.kpi, r.frecuencia
        ])
    ];

    const contenido = filas.map(fila =>
        fila.map(valor =>
            '"' + String(valor || "").replace(/"/g, '""') + '"'
        ).join(",")
    ).join("\r\n");

    const blob = new Blob(
        ["\uFEFF" + contenido],
        { type: "text/csv;charset=utf-8;" }
    );

    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");

    enlace.href = url;
    enlace.download = "Reportes_Analistas.csv";
    enlace.click();

    URL.revokeObjectURL(url);
}
