// src/components/common/Footer.tsx
import React from 'react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-100 text-neutral-600 text-sm mt-12 py-8">
      <div className="container mx-auto px-4 text-center">
        <div className="flex justify-center space-x-4 mb-4">
          <a href="#" className="hover:text-gray-900">법적 책임 고지</a>
          <span>|</span>
          <a href="#" className="hover:text-gray-900">서비스 이용 약관</a>
          <span>|</span>
          <a href="#" className="hover:text-gray-900">개인정보 처리방침</a>
          <span>|</span>
          <a href="#" className="hover:text-gray-900">연락처</a>
          <span>|</span>
          <a href="#" className="hover:text-gray-900">사이트맵</a>
        </div>
        <p className="text-xs">
          © {currentYear} LEH, Inc. All rights reserved.
        </p>
      </div>
    </footer>
  );
};

export default Footer;
