/**
 * LandingFooter Component
 * Plan 3.19.1 - Footer
 *
 * Features:
 * - 3-column layout: Company Info, Links, Legal Notices
 * - Bottom section: Copyright and social media icons
 * - Dark background with light text
 * - Responsive grid layout
 */

import Link from 'next/link';
import { Twitter, Linkedin, Github } from 'lucide-react';

export default function LandingFooter() {
  const companyInfo = {
    name: 'Legal Evidence Hub',
    shortName: 'LEH',
    address: '서울특별시 강남구 테헤란로 123, 10층',
    email: 'contact@legalevidence.hub',
    phone: '02-1234-5678',
  };

  const productLinks = [
    { name: '제품', href: '#features' },
    { name: '가격', href: '#pricing' },
    { name: '블로그', href: '/blog' },
    { name: '고객사례', href: '#testimonials' },
    { name: '채용', href: '/careers' },
  ];

  const legalLinks = [
    { name: '이용약관', href: '/terms' },
    { name: '개인정보처리방침', href: '/privacy' },
    { name: '쿠키정책', href: '/cookies' },
  ];

  const socialLinks = [
    { name: 'Twitter', href: 'https://twitter.com/legalevhub', icon: Twitter },
    { name: 'LinkedIn', href: 'https://linkedin.com/company/legalevhub', icon: Linkedin },
    { name: 'GitHub', href: 'https://github.com/legalevhub', icon: Github },
  ];

  return (
    <footer className="bg-gray-900 text-gray-300 py-12 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-8">
          {/* Company Information Column */}
          <div className="space-y-4">
            <h3 className="text-white text-lg font-bold">{companyInfo.name}</h3>
            <p className="text-sm">{companyInfo.address}</p>
            <p className="text-sm">{companyInfo.email}</p>
            <p className="text-sm">{companyInfo.phone}</p>
          </div>

          {/* Links Column */}
          <div className="space-y-4">
            <h3 className="text-white text-lg font-bold">링크</h3>
            <ul className="space-y-2">
              {productLinks.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-sm hover:text-white transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Notices Column */}
          <div className="space-y-4">
            <h3 className="text-white text-lg font-bold">법적 고지</h3>
            <ul className="space-y-2">
              {legalLinks.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-sm hover:text-white transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-800 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            {/* Copyright */}
            <p className="text-sm text-center md:text-left">
              © 2025 {companyInfo.shortName}. All rights reserved.
            </p>

            {/* Social Media Icons */}
            <div className="flex items-center space-x-4">
              {socialLinks.map((social) => {
                const IconComponent = social.icon;
                return (
                  <Link
                    key={social.name}
                    href={social.href}
                    aria-label={social.name}
                    className="hover:text-white transition-colors"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <IconComponent className="w-5 h-5" />
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
