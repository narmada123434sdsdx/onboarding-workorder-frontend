import { Search } from "lucide-react";
import "./css/home.css";

function Home({user}) {
  return (
    <>
      {/* Search Section */}
      <section className="hero-section text-center text-white py-5">
        <div className="container">
          <h1 className="display-5 fw-bold mb-3">Find Trusted Services Near You</h1>
          <p className="lead mb-4">From home cleaning to beauty & repair – book professionals instantly</p>

          <div className="bg-white rounded-4 p-3 shadow-lg mx-auto search-box">
            <div className="row g-2 align-items-center">
              <div className="col-md-4">
                <input type="text" className="form-control" placeholder="Enter your location" />
              </div>
              <div className="col-md-5">
                <input type="text" className="form-control" placeholder="Search for a service (e.g., AC repair)" />
              </div>
              <div className="col-md-3 d-grid">
                <button className="btn btn-primary d-flex align-items-center justify-content-center">
                  <Search size={18} className="me-2" /> Search
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-5 bg-light">
        <div className="container">
          <h2 className="text-center mb-5 fw-semibold">Our Top Services</h2>
          <div className="row g-4">
            {[
              {
                title: "Home Cleaning",
                img: "../src/assets/images/home_cleaning.jpeg",
                desc: "Professional deep cleaning for a sparkling home.",
              },
              {
                title: "Salon at Home",
                img: "../src/assets/images/home_salon.jpeg",
                desc: "Beauty & grooming by certified experts.",
              },
              {
                title: "AC Repair",
                img: "../src/assets/images/ac_repair.jpeg",
                desc: "Reliable and fast air conditioner servicing.",
              },
              {
                title: "Electrician",
                img: "../src/assets/images/electrician.jpeg",
                desc: "Expert help for wiring, installation & lighting.",
              },
              {
                title: "Plumbing",
                img: "../src/assets/images/plumbing.jpeg",
                desc: "Fix leaks and blockages quickly and affordably.",
              },
              {
                title: "Pest Control",
                img: "../src/assets/images/pest_control.jpeg",
                desc: "Safe and eco-friendly pest removal solutions.",
              },
            ].map((service, index) => (
              <div className="col-12 col-sm-6 col-lg-4" key={index}>
                <div className="card h-100 shadow-sm border-0 service-card">
                  <img src={service.img} className="card-img-top" alt={service.title} />
                  <div className="card-body">
                    <h5 className="card-title">{service.title}</h5>
                    <p className="card-text text-muted">{service.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

export default Home;
