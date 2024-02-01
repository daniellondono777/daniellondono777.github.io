// Open the sidebar by setting its width to 250px and adjusting the left margin of the main content.
function openNav() {
    document.getElementById("mySidebar").style.width = "250px";
    document.getElementById("main").style.marginLeft = "250px";
}

// Close the sidebar by setting its width to 0 and resetting the left margin of the main content to 0.
function closeNav() {
    document.getElementById("mySidebar").style.width = "0";
    document.getElementById("main").style.marginLeft = "0";
}

// Replace text in the specified container based on the parameter (newText).
// Different texts are displayed for each option (1, 2, 3, 4), and a default text for other values.
function replaceText(newText) {
    let text = ''
    if( newText == 1){
        text = `Paragon Cybersecurity collaborated with Microsoft to fortify their digital infrastructure. Our Quantum Resilience Framework, a cutting-edge solution, ensured the resilience of Microsoft's systems against emerging quantum threats. This groundbreaking partnership, valued at 200 million dollars, showcases our commitment to pioneering cybersecurity solutions.`
    }
    else if( newText == 2){
        text = `In a groundbreaking cybersecurity alliance with Tesla, Paragon Cybersecurity deployed our Intrusion Prevention System (IPS) with AI-driven anomaly detection to safeguard Tesla's autonomous vehicle data. This innovative solution, part of a strategic collaboration valued at 300 million dollars, reinforces Tesla's leadership in the automotive industry.`
    }
    else if( newText == 3){
        text = `J.P. Morgan, a global financial powerhouse, entrusted Paragon Cybersecurity with fortifying their digital fortress. Our Advanced Threat Intelligence Platform, deployed in this strategic collaboration, is valued at a staggering 2.3 billion dollars. This underscores our commitment to financial cybersecurity and solidifies our position as a premier partner in safeguarding the world of finance.`
    }
    else if( newText == 4){
        text = 'Saudi Aramco, the energy giant, partnered with Paragon Cybersecurity to secure their critical infrastructure. Our Industrial Control Systems (ICS) Security Suite, a strategic cybersecurity initiative, provided protection against cyber threats targeting the oil and gas sector. This collaboration, valued at 700 million dollars, showcased our expertise in safeguarding critical national infrastructure.'
    }
    else{
        document.getElementById('text-container13').innerHTML = '<h1> Our Clients</h1>'
    }
    document.getElementById('text-container13').innerHTML = '<p>' + text + '</p>';
  }
