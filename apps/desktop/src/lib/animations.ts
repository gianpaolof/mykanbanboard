// lib/animations.ts - Reusable Framer Motion animation configurations

import type { Variants, Transition } from 'framer-motion';

// ===========================================
// TRANSITION PRESETS
// ===========================================

export const springConfig: Transition = {
  type: 'spring',
  stiffness: 300,
  damping: 30,
};

export const springFast: Transition = {
  type: 'spring',
  stiffness: 400,
  damping: 30,
};

export const springBouncy: Transition = {
  type: 'spring',
  stiffness: 200,
  damping: 15,
};

export const easeConfig: Transition = {
  duration: 0.2,
  ease: [0.16, 1, 0.3, 1], // Custom easing (ease-out-expo)
};

export const easeFast: Transition = {
  duration: 0.15,
  ease: 'easeOut',
};

// ===========================================
// STAGGER CONFIGS
// ===========================================

export const staggerConfig = {
  staggerChildren: 0.05,
  delayChildren: 0.1,
};

export const staggerFast = {
  staggerChildren: 0.03,
  delayChildren: 0.05,
};

// ===========================================
// ENTRANCE ANIMATIONS
// ===========================================

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: easeConfig,
  },
};

export const fadeInDown: Variants = {
  hidden: { opacity: 0, y: -20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: easeConfig,
  },
};

export const fadeInLeft: Variants = {
  hidden: { opacity: 0, x: -20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: easeConfig,
  },
};

export const fadeInRight: Variants = {
  hidden: { opacity: 0, x: 20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: easeConfig,
  },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: springConfig,
  },
};

export const scaleInBounce: Variants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: springBouncy,
  },
};

// ===========================================
// LIST/CONTAINER ANIMATIONS
// ===========================================

export const containerStagger: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      ...staggerConfig,
    },
  },
};

export const containerStaggerFast: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      ...staggerFast,
    },
  },
};

export const listItem: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: easeConfig,
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: easeFast,
  },
};

export const listItemScale: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: springConfig,
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: easeFast,
  },
};

// ===========================================
// CARD ANIMATIONS
// ===========================================

export const cardVariants: Variants = {
  initial: { opacity: 0, y: 8 },
  animate: {
    opacity: 1,
    y: 0,
    transition: easeConfig,
  },
  exit: {
    opacity: 0,
    y: -8,
    scale: 0.95,
    transition: easeFast,
  },
  hover: {
    y: -2,
    transition: { duration: 0.2 },
  },
  tap: {
    scale: 0.98,
    transition: { duration: 0.1 },
  },
};

export const cardLiftVariants: Variants = {
  ...cardVariants,
  hover: {
    y: -4,
    scale: 1.02,
    boxShadow: '0 8px 30px rgba(0, 0, 0, 0.3)',
    transition: { duration: 0.2 },
  },
};

// ===========================================
// MODAL ANIMATIONS
// ===========================================

export const modalBackdrop: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: easeFast,
  },
  exit: {
    opacity: 0,
    transition: easeFast,
  },
};

export const modalContent: Variants = {
  hidden: {
    opacity: 0,
    scale: 0.95,
    y: 20,
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      ...easeConfig,
      duration: 0.2,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 20,
    transition: easeFast,
  },
};

export const modalContentStagger: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
};

export const modalField: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: easeConfig,
  },
};

// ===========================================
// SLIDE PANEL ANIMATIONS
// ===========================================

export const slideInRight: Variants = {
  hidden: { x: '100%', opacity: 0 },
  visible: {
    x: 0,
    opacity: 1,
    transition: springConfig,
  },
  exit: {
    x: '100%',
    opacity: 0,
    transition: easeConfig,
  },
};

export const slideInLeft: Variants = {
  hidden: { x: '-100%', opacity: 0 },
  visible: {
    x: 0,
    opacity: 1,
    transition: springConfig,
  },
  exit: {
    x: '-100%',
    opacity: 0,
    transition: easeConfig,
  },
};

export const slideInBottom: Variants = {
  hidden: { y: '100%', opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: springConfig,
  },
  exit: {
    y: '100%',
    opacity: 0,
    transition: easeConfig,
  },
};

// ===========================================
// SKELETON/LOADING ANIMATIONS
// ===========================================

export const skeletonPulse: Variants = {
  animate: {
    opacity: [0.5, 0.8, 0.5],
    transition: {
      repeat: Infinity,
      duration: 1.5,
      ease: 'easeInOut',
    },
  },
};

export const skeletonShimmer = {
  animate: {
    backgroundPosition: ['200% 0', '-200% 0'],
    transition: {
      repeat: Infinity,
      duration: 1.5,
      ease: 'linear',
    },
  },
};

// ===========================================
// NAVIGATION ANIMATIONS
// ===========================================

export const navItem: Variants = {
  hidden: { opacity: 0, x: -10 },
  visible: {
    opacity: 1,
    x: 0,
    transition: easeConfig,
  },
};

export const navSection: Variants = {
  hidden: { opacity: 0, y: -10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      ...easeConfig,
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
};

export const activeIndicator: Transition = {
  type: 'spring',
  stiffness: 300,
  damping: 30,
};

// ===========================================
// DRAG & DROP ANIMATIONS
// ===========================================

export const dragOverlay: Variants = {
  initial: { scale: 1, rotate: 0 },
  animate: {
    scale: 1.05,
    rotate: 2,
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
    transition: springConfig,
  },
};

// ===========================================
// MICRO-INTERACTIONS
// ===========================================

export const buttonHover = {
  scale: 1.02,
  transition: { duration: 0.15 },
};

export const buttonTap = {
  scale: 0.98,
  transition: { duration: 0.1 },
};

export const iconSpin = {
  rotate: 360,
  transition: {
    repeat: Infinity,
    duration: 1,
    ease: 'linear',
  },
};

export const pulseGlow: Variants = {
  animate: {
    boxShadow: [
      '0 0 8px rgba(99, 102, 241, 0.3)',
      '0 0 16px rgba(99, 102, 241, 0.5)',
      '0 0 8px rgba(99, 102, 241, 0.3)',
    ],
    transition: {
      repeat: Infinity,
      duration: 2,
      ease: 'easeInOut',
    },
  },
};

// Critical priority pulse (red glow)
export const criticalPulse: Variants = {
  animate: {
    boxShadow: [
      '0 0 8px rgba(239, 68, 68, 0.5)',
      '0 0 16px rgba(239, 68, 68, 0.8)',
      '0 0 8px rgba(239, 68, 68, 0.5)',
    ],
    transition: {
      repeat: Infinity,
      duration: 2,
      ease: 'easeInOut',
    },
  },
};

// ===========================================
// BOARD-SPECIFIC ANIMATIONS
// ===========================================

export const boardColumn: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: springConfig,
  },
};

export const boardContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.05,
    },
  },
};

// ===========================================
// LABEL ANIMATIONS
// ===========================================

export const labelBadge: Variants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: springFast,
  },
};

export const labelsContainer: Variants = {
  visible: {
    transition: {
      staggerChildren: 0.05,
    },
  },
};
