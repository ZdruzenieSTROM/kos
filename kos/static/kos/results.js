function toggle() {
    document.getElementById("dropdown-content").classList.toggle("show");
}
  
window.onclick = (e) => {
    if (!e.target.matches('.dropdown__button')) {
        let myDropdown = document.getElementById("dropdown-content");
        if (myDropdown.classList.contains('show')) {
            myDropdown.classList.remove('show');
        }
    }
}