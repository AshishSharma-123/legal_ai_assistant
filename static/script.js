<script>
// LOAD HISTORY WHEN PAGE LOADS

window.onload = function () {
    fetch("/history")
        .then(r => r.json())
        .then(data => {
            const list = document.getElementById("historyList");
            list.innerHTML = "";

            data.history.forEach((chat, index) => {
                list.innerHTML += `
                    <div class="historyItem"
                        data-user="${chat.user_message}"
                        data-bot="${chat.bot_reply}"
                        style="
                            background:#fff;
                            padding:10px;
                            margin-bottom:8px;
                            border-radius:6px;
                            cursor:pointer;
                            border:1px solid #ddd;">
                        
                        <strong>${chat.title}</strong><br>
                        <small style="color:gray;">${chat.time}</small>
                    </div>
                `;
            });

            // ON CLICK — SHOW CHAT DETAILS
            document.querySelectorAll(".historyItem").forEach(item => {
                item.addEventListener("click", function () {
                    document.getElementById("chatDisplay").innerHTML = `
                        <div style="
                            background:#f0f0f0;
                            padding:20px;
                            border-radius:10px;">

                            <p><strong>You Asked:</strong></p>
                            <p>${this.dataset.user}</p>

                            <hr>

                            <p><strong>Bot Answer:</strong></p>
                            <p>${this.dataset.bot}</p>
                        </div>
                    `;
                });
            });
        });
};
</script>
