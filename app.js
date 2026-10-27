const mensaje = document.getElementById("mensaje");
const contador = document.getElementById("contador");
const botonLimpiar = document.getElementById("btn-limpiar");
const botonTransmitir = document.getElementById("btn-transmitir");
const estadoTransmision = document.getElementById("estado-transmision");
const bitsAnalizados = document.getElementById("bits-analizados");
const precision = document.getElementById("precision");
const duracion = document.getElementById("duracion");
const mensajeRecuperado = document.getElementById("mensaje-recuperado");
const diagnostico = document.getElementById("diagnostico");
const grafica = document.getElementById("grafica");

const MAX_BYTES = 8;

mensaje.addEventListener("input", () => {
    const bytes = new TextEncoder().encode(mensaje.value).length;
    contador.textContent = `${bytes} / ${MAX_BYTES} bytes`;
});

botonLimpiar.addEventListener("click", () => {
    mensaje.value = "";
    contador.textContent = `0 / ${MAX_BYTES} bytes`;
    estadoTransmision.textContent = "Formulario limpiado.";
    bitsAnalizados.textContent = "—";
    precision.textContent = "—";
    duracion.textContent = "—";
    mensajeRecuperado.textContent = "Esperando una transmisión...";
    diagnostico.textContent = "Todavía no hay datos suficientes para analizar el canal.";
    grafica.innerHTML = '<p class="grafica-vacia">Los intervalos aparecerán aquí después de una transmisión.</p>';
});

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function bitsDesdeTexto(texto) {
    return Array.from(new TextEncoder().encode(texto))
        .map(byte => byte.toString(2).padStart(8, "0"))
        .join("");
}

async function enviarEvento(token, type) {
    const response = await fetch("/api/event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, type })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Falló un evento temporal.");
    return data;
}

function dibujarGrafica(intervalos, umbral) {
    grafica.innerHTML = "";
    grafica.classList.add("grafica-con-datos");
    const max = Math.max(...intervalos, umbral, 0.1);
    intervalos.forEach((intervalo, index) => {
        const barra = document.createElement("div");
        barra.className = "barra " + (intervalo >= umbral ? "color-uno" : "color-cero");
        barra.style.height = `${Math.max(6, (intervalo / max) * 130)}px`;
        barra.title = `Bit ${index + 1}: ${intervalo.toFixed(3)} s`;
        grafica.appendChild(barra);
    });
}

botonTransmitir.addEventListener("click", async () => {
    const texto = mensaje.value;
    if (!texto.trim()) {
        estadoTransmision.textContent = "Escribí un mensaje primero.";
        return;
    }

    const originalBits = bitsDesdeTexto(texto);
    if (originalBits.length > MAX_BYTES * 8) {
        estadoTransmision.textContent = `El mensaje supera el límite de ${MAX_BYTES} bytes UTF-8. Usá un mensaje más corto.`;
        return;
    }

    botonTransmitir.disabled = true;
    botonLimpiar.disabled = true;
    estadoTransmision.textContent = "Preparando sesión y calibrando el canal...";
    bitsAnalizados.textContent = "—";
    precision.textContent = "—";
    duracion.textContent = "—";
    mensajeRecuperado.textContent = "Transmitiendo...";
    diagnostico.textContent = "Se envían señales genéricas; el contenido se representa mediante los intervalos entre solicitudes.";
    grafica.innerHTML = '<p class="grafica-vacia">Midiendo intervalos...</p>';

    const startedAt = performance.now();

    try {
        const startResponse = await fetch("/api/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ bit_count: originalBits.length })
        });
        const startData = await startResponse.json();
        if (!startResponse.ok) throw new Error(startData.error || "No se pudo iniciar la sesión.");

        const token = startData.token;

        // Cuatro eventos rápidos permiten estimar el tiempo base de la red.
        for (let i = 0; i < 4; i++) {
            await enviarEvento(token, "calibration");
        }

        estadoTransmision.textContent = `Transmitiendo ${originalBits.length} bits. No cerrés la página...`;

        for (const bit of originalBits) {
            await sleep(bit === "0" ? 200 : 600);
            // El cuerpo de cada evento no contiene el bit; la diferencia es el tiempo.
            await enviarEvento(token, "bit");
        }

        const finishResponse = await fetch("/api/finish", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token })
        });
        const result = await finishResponse.json();
        if (!finishResponse.ok) throw new Error(result.error || "No se pudo reconstruir el mensaje.");

        const correctBits = originalBits.split("").reduce((total, bit, index) =>
            total + (bit === result.decoded_bits[index] ? 1 : 0), 0);
        const accuracy = (correctBits / originalBits.length) * 100;
        const elapsed = (performance.now() - startedAt) / 1000;

        bitsAnalizados.textContent = `${result.bit_count}`;
        precision.textContent = `${accuracy.toFixed(1)}%`;
        duracion.textContent = `${elapsed.toFixed(2)} s`;
        mensajeRecuperado.textContent = result.recovered_message || "(mensaje vacío)";
        dibujarGrafica(result.intervals, result.threshold);

        diagnostico.textContent =
            `Calibración base: ${result.calibration_baseline.toFixed(3)} s. ` +
            `Umbral: ${result.threshold.toFixed(3)} s. ` +
            `Bits correctos: ${correctBits}/${originalBits.length}. ` +
            (texto === result.recovered_message
                ? "El mensaje se reconstruyó exactamente en esta prueba."
                : "La red afectó la lectura: el mensaje recuperado difiere del original. Repetí la prueba o usá un mensaje más corto.");

        estadoTransmision.textContent = "Transmisión finalizada. Los resultados se calcularon con las mediciones de esta sesión.";
    } catch (error) {
        estadoTransmision.textContent = `Error: ${error.message}`;
        mensajeRecuperado.textContent = "No se pudo recuperar el mensaje.";
        diagnostico.textContent = "Revisá la conexión y volvé a intentar. El primer arranque del alojamiento gratuito puede tardar.";
    } finally {
        botonTransmitir.disabled = false;
        botonLimpiar.disabled = false;
    }
});
