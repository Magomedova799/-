
// ==============================
// DEVSPACE — ГЛАВНАЯ ЛЕНТА
// ==============================

const feed = document.getElementById("feed-container");
const count = document.getElementById("materials-count");

// Тип публикации -> тип в API лайков/комментариев
const CONTENT_TYPES = {
    "Курс": {
        api: "courses",
        likeField: "course_id"
    },
    "Статья": {
        api: "articles",
        likeField: "article_id"
    },
    "Проект": {
        api: "projects",
        likeField: "project_id"
    }
};

// ==============================
// АВТОРИЗАЦИЯ
// ==============================

function getAuthHeaders() {
    const token = localStorage.getItem("access_token");

    if (!token) {
        alert("Чтобы ставить лайки и писать комментарии, войдите в аккаунт.");
        return null;
    }

    return {
        "Authorization": `Bearer ${token}`
    };
}

// ==============================
// ЗАГРУЗКА МОИХ ЛАЙКОВ
// ==============================

async function getMyLikes() {
    const token = localStorage.getItem("access_token");

    if (!token) {
        return [];
    }

    try {
        const response = await fetch("/likes/my", {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            console.error("Не удалось загрузить мои лайки");
            return [];
        }

        return await response.json();

    } catch (error) {
        console.error("Ошибка загрузки лайков:", error);
        return [];
    }
}

// ==============================
// ЗАГРУЗКА МАТЕРИАЛОВ
// ==============================

async function loadMaterials() {
    feed.innerHTML = '<p class="loading">Загружаем публикации...</p>';

    try {
        const endpoints = [
            { url: "/courses/all", type: "Курс" },
            { url: "/articles/all", type: "Статья" },
            { url: "/projects/", type: "Проект" },
            { url: "/polls/all", type: "Опрос" }
        ];

        const responses = await Promise.all(
            endpoints.map(async item => {
                const response = await fetch(item.url);

                if (!response.ok) {
                    throw new Error(`Ошибка загрузки: ${item.type}`);
                }

                const data = await response.json();

                if (!Array.isArray(data)) {
                    throw new Error(`Некорректный ответ API: ${item.type}`);
                }

                return data.map(material => ({
                    ...material,
                    type: item.type
                }));
            })
        );

        const materials = responses.flat();

        materials.sort((a, b) => {
            return new Date(b.created_at || 0) -
                   new Date(a.created_at || 0);
        });

        const myLikes = await getMyLikes();

        renderMaterials(materials, myLikes);

    } catch (error) {
        console.error("Ошибка загрузки ленты:", error);

        feed.innerHTML = `
            <p class="loading">
                Не удалось загрузить публикации.
                Проверь работу сервера.
            </p>
        `;

        count.textContent = "";
    }
}

// ==============================
// ОТОБРАЖЕНИЕ ЛЕНТЫ
// ==============================

function renderMaterials(materials, myLikes = []) {
    feed.innerHTML = "";
    count.textContent = `Материалов: ${materials.length}`;

    if (materials.length === 0) {
        feed.innerHTML = "<p class='loading'>Пока публикаций нет.</p>";
        return;
    }

    materials.forEach(item => {
        const card = document.createElement("article");
        card.className = "material-card";

        const date = item.created_at
            ? new Date(item.created_at).toLocaleDateString("ru-RU")
            : "";

        const header = `
            <div class="card-meta">
                <span>${escapeHTML(item.type)}</span>
                <span>Автор #${escapeHTML(item.user_id)}</span>
                <span>${escapeHTML(date)}</span>
            </div>
        `;

        let content = "";

        // ==========================
        // КУРС
        // ==========================

        if (item.type === "Курс") {
            content = `
                <h3>${escapeHTML(item.title)}</h3>

                <p>${escapeHTML(item.description)}</p>

                <div class="card-footer">
                    <span>
                        ${Number(item.price) === 0
                            ? "Бесплатно"
                            : `${escapeHTML(item.price)} ₽`}
                    </span>

                    <a href="/course/${Number(item.id)}">
                        Открыть курс →
                    </a>
                </div>
            `;
        }

        // ==========================
        // СТАТЬЯ
        // ==========================

        if (item.type === "Статья") {
            content = `
                <h3>${escapeHTML(item.title)}</h3>

                <p>${escapeHTML(item.content)}</p>

                <a href="/article/${Number(item.id)}">
                    Читать далее →
                </a>
            `;
        }

        // ==========================
        // ПРОЕКТ
        // ==========================

        if (item.type === "Проект") {
            content = `
                <h3>${escapeHTML(item.title)}</h3>

                <p>${escapeHTML(item.description)}</p>

                <p class="technologies">
                    ${escapeHTML(item.technologies)}
                </p>

                ${item.image_url
                    ? `
                        <img
                            class="project-image"
                            src="${safeURL(item.image_url)}"
                            alt="Изображение проекта"
                        >
                    `
                    : ""
                }

                <div class="card-links">
                    ${item.github_url
                        ? `
                            <a
                                href="${safeURL(item.github_url)}"
                                target="_blank"
                                rel="noopener noreferrer">
                                GitHub
                            </a>
                        `
                        : ""
                    }

                    ${item.demo_url
                        ? `
                            <a
                                href="${safeURL(item.demo_url)}"
                                target="_blank"
                                rel="noopener noreferrer">
                                Демо
                            </a>
                        `
                        : ""
                    }
                </div>
            `;
        }

        // ==========================
        // ОПРОС
        // ==========================

        if (item.type === "Опрос") {
            const votes = item.votes || {};

            const totalVotes = Object.values(votes)
                .reduce((sum, value) => sum + Number(value || 0), 0);

            content = `
                <h3>${escapeHTML(item.question)}</h3>

                <div class="telegram-poll">

                    ${(item.options || []).map((option, index) => {
                        const optionVotes = Number(
                            votes[String(index)] || 0
                        );

                        const percent = totalVotes > 0
                            ? Math.round(optionVotes / totalVotes * 100)
                            : 0;

                        return `
                            <button
                                class="poll-option"
                                onclick="vote(${Number(item.id)}, ${index}, this)"
                                ${item.is_active ? "" : "disabled"}>

                                <span class="poll-option-name">
                                    ${escapeHTML(option)}
                                </span>

                                <span class="poll-bar">
                                    <span
                                        class="poll-fill"
                                        style="width: ${percent}%">
                                    </span>
                                </span>

                                <span class="poll-result">
                                    <span>${percent}%</span>
                                    <span>${optionVotes} голосов</span>
                                </span>

                            </button>
                        `;
                    }).join("")}

                </div>

                <div class="poll-bottom">
                    <span>${totalVotes} голосов</span>

                    <span>
                        ${item.is_active
                            ? "Опрос открыт"
                            : "Опрос завершён"}
                    </span>
                </div>
            `;
        }

        // ==========================
        // ЛАЙКИ И КОММЕНТАРИИ
        // ==========================

        const config = CONTENT_TYPES[item.type];

        if (config) {
            const liked = myLikes.some(like =>
                like[config.likeField] === item.id
            );

            content += `
                <div class="social-actions">

                    <button
                        class="like-button ${liked ? "liked" : ""}"
                        data-liked="${liked}"
                        onclick="toggleLike('${config.api}', ${Number(item.id)}, this)"
                    >
                        ${liked ? "♥" : "♡"} <span>Нравится</span>
                    </button>

                    <button
                        class="comment-button"
                        onclick="toggleComments('${config.api}', ${Number(item.id)})"
                    >
                        Комментарии
                    </button>

                </div>

                <div
                    class="comments-box"
                    id="comments-${config.api}-${Number(item.id)}"
                    hidden
                ></div>
            `;
        }

        card.innerHTML = header + content;
        feed.appendChild(card);
    });
}

// ==============================
// ЛАЙКИ
// ==============================

async function toggleLike(type, id, button) {
    const headers = getAuthHeaders();

    if (!headers) return;

    const liked = button.dataset.liked === "true";
    const method = liked ? "DELETE" : "POST";

    button.disabled = true;

    try {
        const response = await fetch(`/likes/${type}/${id}`, {
            method: method,
            headers: headers
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Ошибка лайка");
        }

        const newLiked = !liked;

        button.dataset.liked = String(newLiked);
        button.classList.toggle("liked", newLiked);

        button.innerHTML = newLiked
            ? `♥ <span>Нравится</span>`
            : `♡ <span>Нравится</span>`;

    } catch (error) {
        console.error("Ошибка лайка:", error);
        alert(error.message);

    } finally {
        button.disabled = false;
    }
}

// ==============================
// КОММЕНТАРИИ — ОТКРЫТЬ / ЗАКРЫТЬ
// ==============================

async function toggleComments(type, id) {
    const box = document.getElementById(`comments-${type}-${id}`);

    if (!box) return;

    if (!box.hidden) {
        box.hidden = true;
        return;
    }

    box.hidden = false;
    box.innerHTML = '<p class="loading">Загрузка комментариев...</p>';

    await loadComments(type, id, box);
}

// ==============================
// ЗАГРУЗКА КОММЕНТАРИЕВ
// ==============================

async function loadComments(type, id, box) {
    try {
        const response = await fetch(`/comments/${type}/${id}`);

        const comments = await response.json();

        if (!response.ok) {
            throw new Error(
                comments.detail || "Ошибка загрузки комментариев"
            );
        }

        box.innerHTML = `
            <div class="comments-list">
                ${
                    comments.length
                    ? comments.map(comment => `
                        <div class="comment">
                            <strong>${escapeHTML(comment.username)}</strong>
                            <p>${escapeHTML(comment.content)}</p>
                        </div>
                    `).join("")
                    : `
                        <p class="empty-comments">
                            Комментариев пока нет
                        </p>
                    `
                }
            </div>

            <form
                class="comment-form"
                onsubmit="sendComment(event, '${type}', ${id})"
            >
                <input
                    type="text"
                    name="comment"
                    maxlength="2000"
                    placeholder="Написать комментарий..."
                    required
                >

                <button type="submit">Отправить</button>
            </form>
        `;

    } catch (error) {
        console.error("Ошибка комментариев:", error);

        box.innerHTML = `
            <p class="empty-comments">
                ${escapeHTML(error.message)}
            </p>
        `;
    }
}

// ==============================
// ОТПРАВКА КОММЕНТАРИЯ
// ==============================

async function sendComment(event, type, id) {
    event.preventDefault();

    const headers = getAuthHeaders();

    if (!headers) return;

    const form = event.target;
    const input = form.querySelector("input[name='comment']");
    const content = input.value.trim();

    if (!content) return;

    headers["Content-Type"] = "application/json";

    const submitButton = form.querySelector("button");
    submitButton.disabled = true;

    try {
        const response = await fetch(`/comments/${type}/${id}`, {
            method: "POST",
            headers: headers,
            body: JSON.stringify({
                content: content
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Не удалось отправить комментарий"
            );
        }

        const box = document.getElementById(`comments-${type}-${id}`);

        form.reset();

        await loadComments(type, id, box);

    } catch (error) {
        console.error("Ошибка отправки комментария:", error);
        alert(error.message);

    } finally {
        submitButton.disabled = false;
    }
}

// ==============================
// ГОЛОСОВАНИЕ
// ==============================

async function vote(pollId, optionIndex, button) {
    if (button.disabled) return;

    button.disabled = true;

    try {
        const response = await fetch(
            `/polls/${pollId}/vote?option_index=${optionIndex}`,
            {
                method: "POST"
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail || "Не удалось проголосовать"
            );
        }

        await loadMaterials();

    } catch (error) {
        console.error("Ошибка голосования:", error);
        alert(error.message);
        button.disabled = false;
    }
}

// ==============================
// ЗАЩИТА HTML
// ==============================

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[char]);
}

// ==============================
// ПРОВЕРКА ССЫЛОК
// ==============================

function safeURL(value) {
    try {
        const url = new URL(value, window.location.origin);

        if (
            url.protocol === "http:" ||
            url.protocol === "https:"
        ) {
            return escapeHTML(url.href);
        }

    } catch (error) {
        // Некорректная ссылка
    }

    return "#";
}

// ==============================
// СОЗДАНИЕ ПУБЛИКАЦИЙ
// ==============================

function openCreateMenu() {
    alert("Создание публикаций скоро появится!");
}

// ==============================
// ЗАПУСК
// ==============================

loadMaterials();
