import Link from 'next/link';

export default function Home() {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-calm-grey">
            <main className="text-center">
                <h1 className="text-4xl font-bold text-deep-trust-blue mb-4">
                    Legal Evidence Hub
                </h1>
                <p className="text-lg text-gray-600 mb-8">
                    AI-Powered Paralegal System
                </p>
                <Link href="/login" className="btn-primary">
                    로그인하기
                </Link>
            </main>
        </div>
    );
}
