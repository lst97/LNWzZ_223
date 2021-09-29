function send_form() {
    register_form.onsubmit = async (e) => {
        e.preventDefault();
        if(document.getElementById("otp").value.match(/^[0-9]{1,6}$/) != null){
            var query = 'https://127.0.0.1:8443/register?email=' 
                + document.getElementById("email").value.replace("@", "%40") + "&pwd="
                + document.getElementById("pwd").value + "&otp="
                + document.getElementById("otp").value

            let response = await fetch(query, {
                method: 'GET'
            });
            let result = await response.text();
            alert(result);
            if (result == "Register Success, Please login."){
                window.location.replace("https://127.0.0.1:8443/login.html");
            }
            return
        }
    
        alert("OTP format not matched.");
    };
}

function send_otp(){
    register_form.onsubmit = async (e) => {
        e.preventDefault();
        
        document.getElementById("btn_otp").disabled = true;

        let response = await fetch('https://127.0.0.1:8443/otp?email=' + document.getElementById("email").value.replace("@", "%40"), {
            method: 'GET'
        });
    
        let result = await response.text();
        
        alert(result);
    };
}
