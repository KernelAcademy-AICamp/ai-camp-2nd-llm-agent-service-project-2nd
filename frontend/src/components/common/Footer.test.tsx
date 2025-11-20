// src/components/common/Footer.test.tsx
import { render, screen } from '@testing-library/react';
import Footer from './Footer';

describe('plan 3.9: Footer 컴포넌트', () => {
  it('Footer가 렌더링될 때 주요 법적 고지 및 링크를 포함해야 한다.', () => {
    render(<Footer />);

    // 주요 텍스트 존재 여부 확인
    expect(screen.getByText(/법적 책임 고지/i)).toBeInTheDocument();
    expect(screen.getByText(/서비스 이용 약관/i)).toBeInTheDocument();
    expect(screen.getByText(/개인정보 처리방침/i)).toBeInTheDocument();
    expect(screen.getByText(/연락처/i)).toBeInTheDocument();

    // Copyright 텍스트 확인 (연도는 동적으로 변경될 수 있으므로 정규식 사용)
    const year = new Date().getFullYear();
    expect(screen.getByText(new RegExp(`© ${year} LEH, Inc. All rights reserved.`, 'i'))).toBeInTheDocument();
  });

  it('Footer에 사이트맵 링크가 포함되어야 한다.', () => {
    render(<Footer />);

    // 사이트맵 링크 존재 여부 확인
    expect(screen.getByText(/사이트맵/i)).toBeInTheDocument();
  });
});
