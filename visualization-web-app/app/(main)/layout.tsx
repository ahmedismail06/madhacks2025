import Navbar from '@/components/navbar'
import Footer from '@/components/footer'

export default function MainLayout({children}: {children: React.ReactNode}) {
    return (
        <div className="flex flex-col w-7xl mx-auto min-h-screen">
            <Navbar/>
            <main className="flex-1 p-4 bg-siteBackgroundColor">{children}</main>
            <Footer/>
        </div>
    );
}