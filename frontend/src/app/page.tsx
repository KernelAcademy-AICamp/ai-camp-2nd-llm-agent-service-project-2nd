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

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <LandingNav isScrolled={isScrolled} />

      {/* Main Content */}
      <main>
        <HeroSection />
        <SocialProofSection />
        <ProblemStatementSection />
        <SolutionSection />
        <HowItWorksSection />
        <AITransparencySection />
        <PricingSection />
        <TestimonialsSection />
        <FAQSection />
        <FinalCTASection />
      </main>

      {/* Footer */}
      <LandingFooter />
    </div>
  );
}
