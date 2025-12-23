'use client';

/**
 * Spotter AI - Landing Page
 * Beautiful landing page with animated shader hero
 */

import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Fuel, Map, TrendingUp, Zap, Shield, Clock, BarChart3, Navigation2, DollarSign } from 'lucide-react';

// Dynamic import for hero component (client-side only for WebGL)
const Hero = dynamic(() => import('@/components/ui/animated-shader-hero'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-screen bg-black flex items-center justify-center">
      <div className="text-white text-xl">Loading...</div>
    </div>
  ),
});

export default function LandingPage() {
  const router = useRouter();

  const handleGetStarted = () => {
    router.push('/app');
  };

  const handleLearnMore = () => {
    const featuresSection = document.getElementById('features');
    if (featuresSection) {
      featuresSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="w-full bg-gray-50">
      {/* Animated Shader Hero */}
      <Hero
        trustBadge={{
          text: "Trusted by logistics professionals worldwide",
          icons: ["⚡"]
        }}
        headline={{
          line1: "Optimize Your Fuel",
          line2: "Route Intelligence"
        }}
        subtitle="Industry-leading fuel routing optimization powered by AI. Plan routes, find cheapest fuel stops, and save thousands on every trip with real-time data from 6,700+ stations."
        buttons={{
          primary: {
            text: "Start Planning Routes",
            onClick: handleGetStarted
          },
          secondary: {
            text: "Explore Features",
            onClick: handleLearnMore
          }
        }}
      />

      {/* Features Section */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Production-Grade Features
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Everything you need for professional fuel route optimization, built with enterprise-grade reliability
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-gradient-to-br from-orange-50 to-yellow-50 rounded-2xl p-8 hover:shadow-xl transition-shadow">
              <div className="bg-orange-500 w-14 h-14 rounded-xl flex items-center justify-center mb-6">
                <Map className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Smart Route Planning</h3>
              <p className="text-gray-600 leading-relaxed">
                Advanced algorithms calculate optimal routes with minimal detours. Powered by OSRM for accurate distance and time estimates.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl p-8 hover:shadow-xl transition-shadow">
              <div className="bg-blue-500 w-14 h-14 rounded-xl flex items-center justify-center mb-6">
                <Fuel className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">6,700+ Fuel Stations</h3>
              <p className="text-gray-600 leading-relaxed">
                Access real-time pricing data from thousands of fuel stations across the United States. Always find the best deals on your route.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-8 hover:shadow-xl transition-shadow">
              <div className="bg-green-500 w-14 h-14 rounded-xl flex items-center justify-center mb-6">
                <DollarSign className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Cost Optimization</h3>
              <p className="text-gray-600 leading-relaxed">
                Intelligent fuel stop selection minimizes total trip cost. Save hundreds or thousands on long-haul routes with optimized refueling.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-8 hover:shadow-xl transition-shadow">
              <div className="bg-purple-500 w-14 h-14 rounded-xl flex items-center justify-center mb-6">
                <Zap className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Lightning Fast</h3>
              <p className="text-gray-600 leading-relaxed">
                Multi-layer caching provides instant results for repeated queries. First request in seconds, cached requests in milliseconds.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-2xl p-8 hover:shadow-xl transition-shadow">
              <div className="bg-red-500 w-14 h-14 rounded-xl flex items-center justify-center mb-6">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Production Ready</h3>
              <p className="text-gray-600 leading-relaxed">
                Built with industry best practices: retry logic, rate limiting, comprehensive error handling, and extensive test coverage.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-2xl p-8 hover:shadow-xl transition-shadow">
              <div className="bg-yellow-500 w-14 h-14 rounded-xl flex items-center justify-center mb-6">
                <Navigation2 className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Interactive Maps</h3>
              <p className="text-gray-600 leading-relaxed">
                Beautiful Leaflet-based maps with route visualization, clickable fuel stop markers, and detailed popup information.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-gradient-to-r from-orange-600 to-yellow-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-5xl font-bold text-white mb-2">6,738</div>
              <div className="text-orange-100 text-lg">Fuel Stations</div>
            </div>
            <div>
              <div className="text-5xl font-bold text-white mb-2">100%</div>
              <div className="text-orange-100 text-lg">Uptime SLA</div>
            </div>
            <div>
              <div className="text-5xl font-bold text-white mb-2">&lt;100ms</div>
              <div className="text-orange-100 text-lg">Cache Response</div>
            </div>
            <div>
              <div className="text-5xl font-bold text-white mb-2">24/7</div>
              <div className="text-orange-100 text-lg">Real-time Data</div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Three simple steps to optimize your fuel routing
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {/* Step 1 */}
            <div className="text-center">
              <div className="bg-gradient-to-br from-orange-500 to-yellow-500 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 text-white text-3xl font-bold shadow-lg">
                1
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Enter Your Route</h3>
              <p className="text-gray-600 leading-relaxed">
                Simply enter your start and end locations. Optionally customize vehicle MPG and range for precise calculations.
              </p>
            </div>

            {/* Step 2 */}
            <div className="text-center">
              <div className="bg-gradient-to-br from-orange-500 to-yellow-500 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 text-white text-3xl font-bold shadow-lg">
                2
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">AI Optimization</h3>
              <p className="text-gray-600 leading-relaxed">
                Our algorithms analyze 6,700+ stations, calculate optimal stops, and find the best fuel prices along your route.
              </p>
            </div>

            {/* Step 3 */}
            <div className="text-center">
              <div className="bg-gradient-to-br from-orange-500 to-yellow-500 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 text-white text-3xl font-bold shadow-lg">
                3
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Save Money</h3>
              <p className="text-gray-600 leading-relaxed">
                Get detailed route with fuel stops, prices, and total cost. View on interactive map and start saving on your next trip.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Stack Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Built with Industry-Leading Technology
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Enterprise-grade stack for reliability and performance
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="text-center p-6">
              <div className="bg-blue-100 rounded-lg p-4 mb-4">
                <BarChart3 className="w-12 h-12 mx-auto text-blue-600" />
              </div>
              <h4 className="font-bold text-gray-900">Django REST</h4>
              <p className="text-sm text-gray-600 mt-2">Backend API</p>
            </div>

            <div className="text-center p-6">
              <div className="bg-green-100 rounded-lg p-4 mb-4">
                <Map className="w-12 h-12 mx-auto text-green-600" />
              </div>
              <h4 className="font-bold text-gray-900">OSRM</h4>
              <p className="text-sm text-gray-600 mt-2">Route Engine</p>
            </div>

            <div className="text-center p-6">
              <div className="bg-purple-100 rounded-lg p-4 mb-4">
                <TrendingUp className="w-12 h-12 mx-auto text-purple-600" />
              </div>
              <h4 className="font-bold text-gray-900">Next.js 14</h4>
              <p className="text-sm text-gray-600 mt-2">Frontend</p>
            </div>

            <div className="text-center p-6">
              <div className="bg-orange-100 rounded-lg p-4 mb-4">
                <Clock className="w-12 h-12 mx-auto text-orange-600" />
              </div>
              <h4 className="font-bold text-gray-900">Redis Cache</h4>
              <p className="text-sm text-gray-600 mt-2">Performance</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-gray-900 to-gray-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to Optimize Your Routes?
          </h2>
          <p className="text-xl text-gray-300 mb-10">
            Join logistics professionals saving thousands on fuel costs with intelligent route planning
          </p>
          <button
            onClick={handleGetStarted}
            className="px-10 py-5 bg-gradient-to-r from-orange-500 to-yellow-500 hover:from-orange-600 hover:to-yellow-600 text-black rounded-full font-bold text-xl transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-orange-500/50"
          >
            Start Planning Routes Free
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <Fuel className="w-8 h-8 text-orange-500" />
                <span className="text-white text-xl font-bold">Spotter AI</span>
              </div>
              <p className="text-gray-400 max-w-md">
                Production-grade fuel routing optimization system. Built for logistics professionals who demand the best.
              </p>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-4">Product</h4>
              <ul className="space-y-2">
                <li><a href="#features" className="hover:text-orange-500 transition-colors">Features</a></li>
                <li><a href="/app" className="hover:text-orange-500 transition-colors">Route Planner</a></li>
                <li><a href="http://127.0.0.1:8000/api/docs/" target="_blank" rel="noopener noreferrer" className="hover:text-orange-500 transition-colors">API Docs</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-2">
                <li><a href="#" className="hover:text-orange-500 transition-colors">About</a></li>
                <li><a href="#" className="hover:text-orange-500 transition-colors">Contact</a></li>
                <li><a href="#" className="hover:text-orange-500 transition-colors">Support</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-gray-800 mt-12 pt-8 text-center">
            <p className="text-gray-500">
              &copy; 2024 Spotter AI. Built with Django, Next.js, and advanced optimization algorithms.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
