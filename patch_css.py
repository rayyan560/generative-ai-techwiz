import sys

filepath = r'c:\Users\rayyan\Desktop\generative-ai-techwiz-main\static\css\style.css'

animations_css = """

/* ==========================================================================
   ULTRA HIGH GRAPHICS UI ANIMATIONS & MODERN UPGRADES 
   ========================================================================== */

/* Smooth Fade In Keyframes */
@keyframes fadeUp {
  0% { opacity: 0; transform: translateY(30px); }
  100% { opacity: 1; transform: translateY(0); }
}

@keyframes slideInRight {
  0% { opacity: 0; transform: translateX(50px); }
  100% { opacity: 1; transform: translateX(0); }
}

@keyframes pulseGlow {
  0% { box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.4); }
  70% { box-shadow: 0 0 0 15px rgba(79, 70, 229, 0); }
  100% { box-shadow: 0 0 0 0 rgba(79, 70, 229, 0); }
}

@keyframes floating {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}

/* Base Body Improvements for Smoothness */
body {
    scroll-behavior: smooth;
}

/* Card and Container Animations */
.card, .form-container, .dashboard-card, .complaint-box {
    animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

.card:hover, .dashboard-card:hover, .complaint-box:hover {
    transform: translateY(-8px) scale(1.01);
    box-shadow: 0 15px 35px rgba(0,0,0,0.1);
}

/* Enhanced Input Fields */
.form-control, .form-select {
    transition: all 0.3s ease;
    border: 1px solid #e2e8f0;
}
.form-control:focus, .form-select:focus {
    box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.15);
    border-color: #4f46e5;
    transform: translateY(-2px);
}

/* Button Animations & Glassmorphic Hovers */
.btn {
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}

.btn:active {
    transform: scale(0.95);
}

.btn-primary {
    background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
    border: none;
    box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
}

.btn-primary:hover {
    box-shadow: 0 8px 25px rgba(79, 70, 229, 0.5);
    transform: translateY(-3px);
}

/* Adding a shine effect to primary buttons */
.btn-primary::after {
    content: '';
    position: absolute;
    top: -50%;
    left: -60%;
    width: 20%;
    height: 200%;
    background: rgba(255, 255, 255, 0.2);
    transform: rotate(30deg);
    transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}
.btn-primary:hover::after {
    left: 120%;
}

/* Icon Animations inside buttons */
.btn:hover i {
    transform: scale(1.1);
    transition: transform 0.3s ease;
}

/* Nav Item Smooth Underline */
.nav-link {
    position: relative;
    transition: color 0.3s ease;
}

.nav-link::after {
    content: '';
    position: absolute;
    width: 0;
    height: 2px;
    bottom: -4px;
    left: 50%;
    background-color: #4f46e5;
    transition: all 0.3s ease;
}

.nav-link:hover::after, .nav-link.active::after {
    width: 100%;
    left: 0;
}

/* Badge Pulse */
.badge {
    transition: all 0.3s ease;
}
.badge:hover {
    transform: scale(1.1);
}
.badge.bg-primary {
    animation: pulseGlow 2s infinite;
}

/* Table Row Hover Animations */
.table tbody tr {
    transition: background-color 0.3s ease, transform 0.3s ease;
}
.table tbody tr:hover {
    background-color: rgba(79, 70, 229, 0.03);
    transform: scale(1.005);
    cursor: pointer;
}

/* Hero Section or Images floating effect */
.hero-image, .floating-img {
    animation: floating 4s ease-in-out infinite;
}

/* Success / Alert Boxes */
.alert {
    animation: slideInRight 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    box-shadow: 0 10px 30px rgba(0,0,0,0.08);
}

/* Progress Step Bars */
.step-item {
    transition: all 0.4s ease;
}
.step-item.active {
    transform: scale(1.05);
    font-weight: bold;
}
.step-item.active .step-icon {
    animation: pulseGlow 2s infinite;
}

"""

with open(filepath, 'a', encoding='utf-8') as f:
    f.write(animations_css)

print('Ultra High Graphics CSS appended.')
