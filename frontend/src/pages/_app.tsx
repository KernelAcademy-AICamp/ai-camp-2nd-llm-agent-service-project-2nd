import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import Head from 'next/head';
import Footer from '@/components/common/Footer';

export default function App({ Component, pageProps }: AppProps) {
    return (
        <>
            <Head>
                <title>Legal Evidence Hub</title>
                <meta name="viewport" content="width=device-width, initial-scale=1" />
            </Head>
            <div className="flex flex-col min-h-screen">
                <main className="flex-grow">
                    <Component {...pageProps} />
                </main>
                <Footer />
            </div>
        </>
    );
}
