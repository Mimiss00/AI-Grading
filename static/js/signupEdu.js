const forms = document.querySelector(".forms"),
    pwShowHide = document.querySelectorAll(".eye-icon"),
    signupLinks = document.querySelectorAll(".signup-link");

// Toggle password visibility
pwShowHide.forEach(icon => {
    icon.addEventListener("click", () => {
        let pwInput = icon.parentElement.querySelector("input");
        if (pwInput.type === "password") {
            pwInput.type = "text";
            icon.classList.replace("bxs-hide", "bxs-show");
        } else {
            pwInput.type = "password";
            icon.classList.replace("bxs-show", "bxs-hide");
        }
    });
});

// Toggle between login/signup
signupLinks.forEach(link => {
    link.addEventListener("click", e => {
        e.preventDefault();
        forms.classList.toggle("show-signup");
    });
});
