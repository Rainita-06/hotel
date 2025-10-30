// /* Modal Manager - Centralized modal functionality using Tailwind CSS transitions */

// const ModalManager = {
//   open: function(id) {
//     const modal = document.getElementById(id);
//     if (!modal) return;
//     const modalContent = modal.querySelector('div[onclick]');
//     modal.classList.remove('hidden');
//     modal.classList.add('flex');
//     // Trigger reflow and start transition
//     requestAnimationFrame(() => {
//       modal.classList.remove('opacity-0');
//       if (modalContent) {
//         modalContent.classList.remove('scale-95', 'opacity-0');
//         modalContent.classList.add('scale-100', 'opacity-100');
//       }
//     });
//   },
//   close: function(id) {
//     const modal = document.getElementById(id);
//     if (!modal) return;
//     const modalContent = modal.querySelector('div[onclick]');
//     modal.classList.add('opacity-0');
//     if (modalContent) {
//       modalContent.classList.remove('scale-100', 'opacity-100');
//       modalContent.classList.add('scale-95', 'opacity-0');
//     }
//     // After transition delay, hide the modal
//     setTimeout(() => {
//       modal.classList.add('hidden');
//       modal.classList.remove('flex');
//     }, 300);
//   },
//   toast: function(message, type = 'success') {
//     const toast = document.getElementById('toastNotification');
//     const toastMessage = document.getElementById('toastMessage');
//     if (!toast || !toastMessage) return;
//     toastMessage.textContent = message;
//     toast.classList.remove('bg-green-500', 'bg-red-500');
//     if (type === 'error') {
//       toast.classList.add('bg-red-500');
//     } else {
//       toast.classList.add('bg-green-500');
//     }
//     toast.classList.remove('translate-x-full', 'opacity-0');
//     setTimeout(() => {
//       toast.classList.add('translate-x-full', 'opacity-0');
//     }, 3000);
//   }
// };

// // Expose globally on DOMContentLoaded to ensure elements are available
// document.addEventListener('DOMContentLoaded', function() {
//   window.showModal = function(id) { ModalManager.open(id); };
//   window.closeModal = function(id) { ModalManager.close(id); };
//   window.showToast = function(message, type) { ModalManager.toast(message, type); };
// });
/* Modal Manager - Centralized modal functionality using Tailwind CSS transitions */

const ModalManager = {
  open: function(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    const modalContent = modal.querySelector('div[onclick]');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    // Trigger reflow and start transition
    requestAnimationFrame(() => {
      modal.classList.remove('opacity-0');
      if (modalContent) {
        modalContent.classList.remove('scale-95', 'opacity-0');
        modalContent.classList.add('scale-100', 'opacity-100');
      }
    });
  },
  close: function(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    const modalContent = modal.querySelector('div[onclick]');
    modal.classList.add('opacity-0');
    if (modalContent) {
      modalContent.classList.remove('scale-100', 'opacity-100');
      modalContent.classList.add('scale-95', 'opacity-0');
    }
    // After transition delay, hide the modal
    setTimeout(() => {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }, 300);
  },
  toast: function(message, type = 'success') {
    // Use the global showToast function if available, otherwise use the local implementation
    if (typeof window.showToast === 'function') {
      window.showToast(message, type);
    } else {
      // Fallback implementation
      const toast = document.getElementById('toastNotification');
      const toastMessage = document.getElementById('toastMessage');
      if (!toast || !toastMessage) return;
      toastMessage.textContent = message;
      toast.classList.remove('bg-green-500', 'bg-red-500');
      if (type === 'error') {
        toast.classList.add('bg-red-500');
      } else {
        toast.classList.add('bg-green-500');
      }
      toast.classList.remove('translate-x-full', 'opacity-0');
      setTimeout(() => {
        toast.classList.add('translate-x-full', 'opacity-0');
      }, 3000);
    }
  }
};

// Expose globally on DOMContentLoaded to ensure elements are available
document.addEventListener('DOMContentLoaded', function() {
  window.showModal = function(id) { ModalManager.open(id); };
  window.closeModal = function(id) { ModalManager.close(id); };
  window.showToast = function(message, type) { ModalManager.toast(message, type); };
});