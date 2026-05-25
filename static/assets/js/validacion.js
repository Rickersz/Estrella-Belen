/**
 * validacion.js
 * Validación de formularios en cliente (ítem 13) y
 * sistema de toasts/tooltips (ítem 7)
 * Sistema Escolar Estrella de Belén
 */

'use strict';

/* ─── TOAST ──────────────────────────────────────────────────────────────── */

function mostrarToast(mensaje, tipo = 'info', duracion = 4000) {
  let contenedor = document.getElementById('toast-container-sistema');
  if (!contenedor) {
    contenedor = document.createElement('div');
    contenedor.id = 'toast-container-sistema';
    contenedor.className = 'toast-container-sistema';
    document.body.appendChild(contenedor);
  }

  const iconos = {
    exito: 'fa-check-circle',
    error: 'fa-exclamation-circle',
    info:  'fa-info-circle',
    aviso: 'fa-exclamation-triangle',
  };

  const toast = document.createElement('div');
  toast.className = `toast-sistema ${tipo}`;
  toast.innerHTML = `
    <i class="fas ${iconos[tipo] || iconos.info} toast-icono ${tipo}" style="font-size:1.1rem;flex-shrink:0"></i>
    <span style="flex:1">${mensaje}</span>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;color:var(--s-suave);cursor:pointer;padding:0;font-size:1rem">
      <i class="fas fa-times"></i>
    </button>
  `;

  contenedor.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('saliendo');
    setTimeout(() => toast.remove(), 300);
  }, duracion);
}

/* ─── FORTALEZA DE CONTRASEÑA ────────────────────────────────────────────── */

function calcularFortaleza(password) {
  let puntos = 0;
  if (password.length >= 16) puntos++;
  if (password.length >= 24) puntos++;
  if (/[A-Z]/.test(password)) puntos++;
  if (/[a-z]/.test(password)) puntos++;
  if (/[0-9]/.test(password)) puntos++;
  if (/[^A-Za-z0-9]/.test(password)) puntos++;
  return puntos;
}

function mostrarFortaleza(input) {
  let contenedor = input.parentElement.querySelector('.fortaleza-contrasena');
  if (!contenedor) {
    contenedor = document.createElement('div');
    contenedor.className = 'fortaleza-contrasena';
    contenedor.innerHTML = `
      <div class="fortaleza-barra">
        <div class="fortaleza-relleno"></div>
      </div>
      <span class="fortaleza-texto"></span>
    `;
    input.parentElement.appendChild(contenedor);
  }

  const relleno = contenedor.querySelector('.fortaleza-relleno');
  const texto   = contenedor.querySelector('.fortaleza-texto');
  const puntos  = calcularFortaleza(input.value);

  const niveles = [
    { max: 1, color: '#ef4444', label: 'Muy débil',  pct: '16%' },
    { max: 2, color: '#f97316', label: 'Débil',       pct: '33%' },
    { max: 3, color: '#F7CF0D', label: 'Regular',     pct: '50%' },
    { max: 4, color: '#7DC7F6', label: 'Buena',       pct: '66%' },
    { max: 5, color: '#8BF4ED', label: 'Fuerte',      pct: '83%' },
    { max: 6, color: '#B4F5D5', label: 'Muy fuerte',  pct: '100%' },
  ];

  const nivel = niveles.find(n => puntos <= n.max) || niveles[5];
  relleno.style.width      = nivel.pct;
  relleno.style.background = nivel.color;
  texto.textContent        = input.value ? `Fortaleza: ${nivel.label}` : '';
  texto.style.color        = nivel.color;
}

/* ─── VALIDAR CAMPO INDIVIDUAL ───────────────────────────────────────────── */

function validarCampo(input) {
  const valor = input.value.trim();
  let error   = '';

  // Requerido
  if (input.required && !valor) {
    error = 'Este campo es obligatorio.';
  }

  // Email
  else if (input.type === 'email' && valor) {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor)) {
      error = 'Ingresa un correo electrónico válido.';
    }
  }

  // Contraseña mínimo 16 caracteres
  else if (input.type === 'password' && valor && input.dataset.minlength) {
    const min = parseInt(input.dataset.minlength);
    if (valor.length < min) {
      error = `La contraseña debe tener al menos ${min} caracteres.`;
    }
  }

  // Número
  else if (input.type === 'number' && valor) {
    if (isNaN(parseFloat(valor))) {
      error = 'Ingresa un número válido.';
    }
    if (input.min && parseFloat(valor) < parseFloat(input.min)) {
      error = `El valor mínimo es ${input.min}.`;
    }
  }

  // Teléfono
  else if (input.dataset.tipo === 'telefono' && valor) {
    if (!/^\d{7,15}$/.test(valor.replace(/[\s\-\+\(\)]/g, ''))) {
      error = 'Ingresa un número de teléfono válido.';
    }
  }

  // Cédula
  else if (input.dataset.tipo === 'cedula' && valor) {
    if (!/^\d{6,10}$/.test(valor)) {
      error = 'La cédula debe tener entre 6 y 10 dígitos.';
    }
  }

  mostrarErrorCampo(input, error);
  return !error;
}

function mostrarErrorCampo(input, mensaje) {
  input.classList.remove('campo-invalido', 'campo-valido');

  let msgEl = input.parentElement.querySelector('.mensaje-validacion');
  if (!msgEl) {
    msgEl = document.createElement('div');
    msgEl.className = 'mensaje-validacion';
    input.parentElement.appendChild(msgEl);
  }

  if (mensaje) {
    input.classList.add('campo-invalido');
    msgEl.className = 'mensaje-validacion error visible';
    msgEl.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${mensaje}`;
  } else if (input.value.trim()) {
    input.classList.add('campo-valido');
    msgEl.className = 'mensaje-validacion exito visible';
    msgEl.innerHTML = `<i class="fas fa-check-circle"></i> Correcto`;
  } else {
    msgEl.className = 'mensaje-validacion';
    msgEl.innerHTML = '';
  }
}

/* ─── INICIALIZAR VALIDACIÓN EN FORMULARIOS ──────────────────────────────── */

function inicializarValidacion(formulario) {
  if (!formulario) return;

  const campos = formulario.querySelectorAll('input, select, textarea');

  campos.forEach(campo => {
    // Validar al perder el foco
    campo.addEventListener('blur', () => validarCampo(campo));

    // Fortaleza de contraseña en tiempo real
    if (campo.type === 'password') {
      campo.addEventListener('input', () => mostrarFortaleza(campo));
    }

    // Limpiar error al escribir
    campo.addEventListener('input', () => {
      if (campo.classList.contains('campo-invalido')) {
        validarCampo(campo);
      }
    });
  });

  // Validar todo al enviar
  formulario.addEventListener('submit', function (e) {
    let valido = true;
    campos.forEach(campo => {
      if (!validarCampo(campo)) valido = false;
    });

    if (!valido) {
      e.preventDefault();
      mostrarToast('Por favor corrige los errores antes de continuar.', 'error');
      // Scroll al primer error
      const primerError = formulario.querySelector('.campo-invalido');
      if (primerError) {
        primerError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        primerError.focus();
      }
    }
  });
}

/* ─── AUTO-INICIALIZAR AL CARGAR ─────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function () {

  // Inicializar validación en todos los formularios con data-validar
  document.querySelectorAll('form[data-validar]').forEach(inicializarValidacion);

  // Mostrar toasts desde mensajes Django (si existen en el DOM)
  document.querySelectorAll('[data-toast]').forEach(el => {
    mostrarToast(el.dataset.toast, el.dataset.tipo || 'info');
    el.remove();
  });

  // Confirmar acciones peligrosas
  document.querySelectorAll('[data-confirmar]').forEach(btn => {
    btn.addEventListener('click', function (e) {
      if (!confirm(this.dataset.confirmar)) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  });

});

// Exportar para uso global
window.mostrarToast = mostrarToast;
