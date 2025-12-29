/**
 * Landing Page - Main Entry Point
 * Plan 3.19.2 - Technical Requirements
 *
 * Features:
 * - Integrated landing page with all 12 sections
 * - SEO optimization with metadata
 * - Scroll tracking for navigation
 * - Performance optimizations
 */

'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import LandingNav from '@/components/landing/LandingNav';
import HeroSection from '@/components/landing/HeroSection';
import SocialProofSection from '@/components/landing/SocialProofSection';
import ProblemStatementSection from '@/components/landing/ProblemStatementSection';
import SolutionSection from '@/components/landing/SolutionSection';
import HowItWorksSection from '@/components/landing/HowItWorksSection';
import AITransparencySection from '@/components/landing/AITransparencySection';
import PricingSection from '@/components/landing/PricingSection';
import TestimonialsSection from '@/components/landing/TestimonialsSection';
import FAQSection from '@/components/landing/FAQSection';
import FinalCTASection from '@/components/landing/FinalCTASection';
import LandingFooter from '@/components/landing/LandingFooter';

export default function LandingPage() {
  const [isScrolled, setIsScrolled] = useState(false);
  const { isAuthenticated, logout, isLoading } = useAuth();


  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Intersection Observer for scroll animations
  useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: '0px',
      threshold: 0.1,
    };

    const observerCallback = (entries: IntersectionObserverEntry[]) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-in');
          entry.target.setAttribute('data-animated', 'true');
        }
      });
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);

    // Observe all sections with data-animate attribute
    const sections = document.querySelectorAll('[data-animate]');
    sections.forEach((section) => observer.observe(section));

    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <LandingNav
        isScrolled={isScrolled}
        isAuthenticated={isAuthenticated}
        authLoading={isLoading}
        onLogout={logout}
      />

      {/* Main Content */}
      <main>
        <div data-animate="hero">
          <HeroSection />
        </div>
        <div data-animate="social-proof">
          <SocialProofSection />
        </div>
        <div data-animate="problem">
          <ProblemStatementSection />
        </div>
        <div data-animate="solution">
          <SolutionSection />
        </div>
        <div data-animate="how-it-works">
          <HowItWorksSection />
        </div>
        <div data-animate="ai-transparency">
          <AITransparencySection />
        </div>
        <div data-animate="pricing">
          <PricingSection />
        </div>
        <div data-animate="testimonials">
          <TestimonialsSection />
        </div>
        <div data-animate="faq">
          <FAQSection />
        </div>
        <div data-animate="cta">
          <FinalCTASection />
        </div>
      </main>

      {/* Footer */}
      <LandingFooter />
    </div>
  );
}
