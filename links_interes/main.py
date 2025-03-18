import tkinter as tk
from tkinter import ttk, messagebox
# Importamos mysql.connector en lugar de sqlite3
import mysql.connector
from mysql.connector import Error, IntegrityError  # <-- Para manejar excepciones específicas
# import sqlite3
from datetime import datetime

class LinksDeInteresApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Links de Interés")
        self.root.geometry("800x600")

        # Inicializar la base de datos
        self.init_database()

        # Crear interfaz gráfica
        self.create_widgets()

        # Cargar datos iniciales
        self.load_data()

    def init_database(self):
        """        Inicializa la conexión a la base de datos MySQL y crea las tablas si no existen."""
        # self.conn = sqlite3.connect('links_interes.db')

        try:
            # 2) Conexión a MySQL
            self.conn = mysql.connector.connect(
                host="localhost",  # <-- Ajusta según tu entorno
                user="root",  # <-- Cambia por tu usuario de MySQL
                password="",  # <-- Cambia por tu contraseña (si tienes)
                database="links_db"  # <-- Debe existir previamente
            )
            self.cursor = self.conn.cursor()

        except Error as e:
            messagebox.showerror("Error de conexión", f"No se pudo conectar a MySQL: {e}")
            return

        #  Crear tablas en MySQL (adaptadas de SQLite a MySQL)
        # - Usamos tipos VARCHAR en lugar de TEXT para llaves primarias o foráneas.
        # - Cambiamos INTEGER PRIMARY KEY AUTOINCREMENT a INT AUTO_INCREMENT.
        # - Añadimos ENGINE=InnoDB para soportar claves foráneas.
        # - MySQL no entiende AUTOINCREMENT como en SQLite, se usa AUTO_INCREMENT.

        # Tabla usuario
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuario (
                    id VARCHAR(30) NOT NULL,
                    nombre VARCHAR(100) NOT NULL,
                    apellido VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE,
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB
            ''')

        # Tabla multimedia
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS multimedia (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tipo VARCHAR(50) NOT NULL
                ) ENGINE=InnoDB
            ''')

        # Tabla links
        # Nota: Para la columna fecha, usamos DATE con DEFAULT CURDATE()
        # (si tu versión de MySQL lo soporta).
        # Si da error de sintaxis, podrías dejarla como DATE sin default
        # y asignar la fecha en tu código Python.
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS links (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario_id VARCHAR(30) NOT NULL,
                    link TEXT NOT NULL,
                    multimedia_id INT NOT NULL,
                    fecha DATE DEFAULT (CURDATE()),
                    autor VARCHAR(100),
                    descripcion TEXT,
                    tema VARCHAR(100),
                    FOREIGN KEY (usuario_id) REFERENCES usuario(id),
                    FOREIGN KEY (multimedia_id) REFERENCES multimedia(id)
                ) ENGINE=InnoDB
            ''')

        # Verificar si existen tipos de multimedia, si no, agregar tipos por defecto
        self.cursor.execute("SELECT COUNT(*) FROM multimedia")
        count = self.cursor.fetchone()[0]
        if count == 0:
            multimedia_types = ['Audio', 'Video', 'Imagen', 'Documento', 'Otro']
            for tipo in multimedia_types:
                self.cursor.execute("INSERT INTO multimedia (tipo) VALUES (%s)", (tipo,))

        self.conn.commit()

    def create_widgets(self):
        """Crea todos los widgets de la interfaz gráfica"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Crear pestañas
        self.tab_usuarios = ttk.Frame(notebook)
        self.tab_links = ttk.Frame(notebook)

        notebook.add(self.tab_usuarios, text="Gestión de Usuarios")
        notebook.add(self.tab_links, text="Gestión de Links")

        # Configurar pestaña de Usuarios
        self.setup_usuarios_tab()

        # Configurar pestaña de Links
        self.setup_links_tab()

    def setup_usuarios_tab(self):
        """Configura la pestaña de gestión de usuarios"""
        # Formulario de usuario
        form_frame = ttk.LabelFrame(self.tab_usuarios, text="Formulario de Usuario")
        form_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(form_frame, text="Cédula/ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.user_id_entry = ttk.Entry(form_frame, width=30)
        self.user_id_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Nombre:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.nombre_entry = ttk.Entry(form_frame, width=30)
        self.nombre_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Apellido:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.apellido_entry = ttk.Entry(form_frame, width=30)
        self.apellido_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Email:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.email_entry = ttk.Entry(form_frame, width=30)
        self.email_entry.grid(row=3, column=1, padx=5, pady=5)

        # Frame de botones
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(buttons_frame, text="Guardar", command=self.save_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Actualizar", command=self.update_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Eliminar", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Limpiar", command=self.clear_user_form).pack(side=tk.LEFT, padx=5)

        # Tabla de usuarios
        table_frame = ttk.LabelFrame(self.tab_usuarios, text="Lista de Usuarios")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ('id', 'nombre', 'apellido', 'email')
        self.users_table = ttk.Treeview(table_frame, columns=columns, show='headings')

        # Definir encabezados
        self.users_table.heading('id', text='Cédula/ID')
        self.users_table.heading('nombre', text='Nombre')
        self.users_table.heading('apellido', text='Apellido')
        self.users_table.heading('email', text='Email')

        # Definir columnas
        self.users_table.column('id', width=100)
        self.users_table.column('nombre', width=150)
        self.users_table.column('apellido', width=150)
        self.users_table.column('email', width=200)

        self.users_table.pack(fill="both", expand=True)

        # Vincular evento de selección
        self.users_table.bind('<<TreeviewSelect>>', self.on_user_select)

        # Añadir barra de desplazamiento
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.users_table.yview)
        self.users_table.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_links_tab(self):
        """Configura la pestaña de gestión de links"""
        # Formulario de link
        form_frame = ttk.LabelFrame(self.tab_links, text="Formulario de Links")
        form_frame.pack(fill="x", padx=10, pady=10)

        # Selección de usuario
        ttk.Label(form_frame, text="Usuario:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.user_combo = ttk.Combobox(form_frame, width=30, state="readonly")
        self.user_combo.grid(row=0, column=1, padx=5, pady=5)

        # Link
        ttk.Label(form_frame, text="Link:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.link_entry = ttk.Entry(form_frame, width=50)
        self.link_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        # Tipo de multimedia
        ttk.Label(form_frame, text="Tipo Multimedia:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.multimedia_combo = ttk.Combobox(form_frame, width=30, state="readonly")
        self.multimedia_combo.grid(row=2, column=1, padx=5, pady=5)

        # Autor
        ttk.Label(form_frame, text="Autor:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.autor_entry = ttk.Entry(form_frame, width=30)
        self.autor_entry.grid(row=3, column=1, padx=5, pady=5)

        # Fecha
        ttk.Label(form_frame, text="Fecha:").grid(row=3, column=2, padx=5, pady=5, sticky="w")
        self.fecha_entry = ttk.Entry(form_frame, width=15)
        self.fecha_entry.grid(row=3, column=3, padx=5, pady=5)
        self.fecha_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Descripción
        ttk.Label(form_frame, text="Descripción:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.descripcion_text = tk.Text(form_frame, width=50, height=3)
        self.descripcion_text.grid(row=4, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Tema
        ttk.Label(form_frame, text="Tema:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.tema_entry = ttk.Entry(form_frame, width=30)
        self.tema_entry.grid(row=5, column=1, padx=5, pady=5)

        # Campo oculto para ID en actualizaciones
        self.link_id_var = tk.StringVar()

        # Frame de botones
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=6, column=0, columnspan=4, pady=10)

        ttk.Button(buttons_frame, text="Guardar", command=self.save_link).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Actualizar", command=self.update_link).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Eliminar", command=self.delete_link).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Limpiar", command=self.clear_link_form).pack(side=tk.LEFT, padx=5)

        # Tabla de links
        table_frame = ttk.LabelFrame(self.tab_links, text="Lista de Links")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ('id', 'usuario', 'link', 'multimedia', 'fecha', 'autor', 'tema')
        self.links_table = ttk.Treeview(table_frame, columns=columns, show='headings')

        # Definir encabezados
        self.links_table.heading('id', text='ID')
        self.links_table.heading('usuario', text='Usuario')
        self.links_table.heading('link', text='Link')
        self.links_table.heading('multimedia', text='Tipo')
        self.links_table.heading('fecha', text='Fecha')
        self.links_table.heading('autor', text='Autor')
        self.links_table.heading('tema', text='Tema')

        # Definir columnas
        self.links_table.column('id', width=50)
        self.links_table.column('usuario', width=100)
        self.links_table.column('link', width=200)
        self.links_table.column('multimedia', width=80)
        self.links_table.column('fecha', width=80)
        self.links_table.column('autor', width=100)
        self.links_table.column('tema', width=100)

        self.links_table.pack(fill="both", expand=True)

        # Vincular evento de selección
        self.links_table.bind('<<TreeviewSelect>>', self.on_link_select)

        # Añadir barra de desplazamiento
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.links_table.yview)
        self.links_table.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_data(self):
        """Carga todos los datos de la base de datos"""
        self.load_users()
        self.load_multimedia_types()
        self.load_links()

    def load_users(self):
        """Carga usuarios desde la base de datos a la tabla y combo"""
        # Limpiar la tabla
        for item in self.users_table.get_children():
            self.users_table.delete(item)

        # Obtener usuarios de la BD
        self.cursor.execute("SELECT id, nombre, apellido, email FROM usuario")
        users = self.cursor.fetchall()

        # Insertar en tabla
        for user in users:
            self.users_table.insert('', 'end', values=user)

        # Actualizar el combobox
        self.user_combo['values'] = [f"{user[0]} - {user[1]} {user[2]}" for user in users]

    def load_multimedia_types(self):
        """Carga tipos de multimedia desde la base de datos al combo"""
        # Obtener tipos de multimedia de la BD
        self.cursor.execute("SELECT id, tipo FROM multimedia")
        types = self.cursor.fetchall()

        # Actualizar el combobox
        self.multimedia_combo['values'] = [f"{t[0]} - {t[1]}" for t in types]

    def load_links(self):
        """Carga links desde la base de datos a la tabla de links"""
        # Limpiar la tabla
        for item in self.links_table.get_children():
            self.links_table.delete(item)

        # Unimos las tablas links, usuario y multimedia
        self.cursor.execute("""
                SELECT l.id,
                       CONCAT(u.nombre, ' ', u.apellido) AS usuario,
                       l.link,
                       m.tipo,
                       l.fecha,
                       l.autor,
                       l.tema
                FROM links l
                JOIN usuario u ON l.usuario_id = u.id
                JOIN multimedia m ON l.multimedia_id = m.id
            """)
        links = self.cursor.fetchall()

        # Insertar en tabla
        for link in links:
            self.links_table.insert('', 'end', values=link)

    def save_user(self):
        """Guarda un nuevo usuario en la base de datos"""
        user_id = self.user_id_entry.get().strip()
        nombre = self.nombre_entry.get().strip()
        apellido = self.apellido_entry.get().strip()
        email = self.email_entry.get().strip()

        if not user_id or not nombre or not apellido:
            messagebox.showerror("Error", "Los campos ID, Nombre y Apellido son obligatorios")
            return

        try:
            self.cursor.execute(
                "INSERT INTO usuario (id, nombre, apellido, email) VALUES (%s, %s, %s, %s)",
                (user_id, nombre, apellido, email)
            )
            self.conn.commit()
            messagebox.showinfo("Éxito", "Usuario guardado correctamente")
            self.clear_user_form()
            self.load_users()
        except IntegrityError:
            # Manejo de error por violación de PK o UNIQUE
            messagebox.showerror("Error", "El ID o Email ya existe en la base de datos")
        except Error as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")

    def update_user(self):
        """Actualiza un usuario existente"""
        user_id = self.user_id_entry.get().strip()
        nombre = self.nombre_entry.get().strip()
        apellido = self.apellido_entry.get().strip()
        email = self.email_entry.get().strip()

        if not user_id or not nombre or not apellido:
            messagebox.showerror("Error", "Los campos ID, Nombre y Apellido son obligatorios")
            return

        try:
            self.cursor.execute(
                "UPDATE usuario SET nombre = %s, apellido = %s, email = %s WHERE id = %s",
                (nombre, apellido, email, user_id)
            )
            if self.cursor.rowcount == 0:
                messagebox.showerror("Error", "Usuario no encontrado")
                return

            self.conn.commit()
            messagebox.showinfo("Éxito", "Usuario actualizado correctamente")
            self.clear_user_form()
            self.load_users()
            self.load_links()  # Recargar links ya que muestran el nombre de usuario
        except Error as e:
            messagebox.showerror("Error", f"Error al actualizar: {str(e)}")

    def delete_user(self):
        """Elimina un usuario"""
        user_id = self.user_id_entry.get().strip()

        if not user_id:
            messagebox.showerror("Error", "Seleccione un usuario para eliminar")
            return

        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar",
                                   "¿Está seguro de eliminar este usuario? Se eliminarán también todos sus links."):
            return

        try:
            # Eliminar manualmente sus links si no tuvieras ON DELETE CASCADE:
            # self.cursor.execute("DELETE FROM links WHERE usuario_id = %s", (user_id,))

            self.cursor.execute("DELETE FROM usuario WHERE id = %s", (user_id,))
            self.conn.commit()

            if self.cursor.rowcount == 0:
                messagebox.showerror("Error", "Usuario no encontrado")
                return

            messagebox.showinfo("Éxito", "Usuario eliminado correctamente")
            self.clear_user_form()
            self.load_users()
            self.load_links()
        except Error as e:
            messagebox.showerror("Error", f"Error al eliminar: {str(e)}")

    def save_link(self):
        """Guarda un nuevo link en la base de datos"""
        # Obtener datos del formulario
        if not self.user_combo.get():
            messagebox.showerror("Error", "Debe seleccionar un usuario")
            return

        if not self.multimedia_combo.get():
            messagebox.showerror("Error", "Debe seleccionar un tipo de multimedia")
            return

        link = self.link_entry.get().strip()
        if not link:
            messagebox.showerror("Error", "El campo link es obligatorio")
            return

        # Extraer IDs de las selecciones de combo
        user_id = self.user_combo.get().split(' - ')[0]
        multimedia_id = self.multimedia_combo.get().split(' - ')[0]

        fecha = self.fecha_entry.get().strip()
        autor = self.autor_entry.get().strip()
        descripcion = self.descripcion_text.get("1.0", "end-1c").strip()
        tema = self.tema_entry.get().strip()

        try:
            self.cursor.execute(
                """INSERT INTO links
                   (usuario_id, link, multimedia_id, fecha, autor, descripcion, tema)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (user_id, link, multimedia_id, fecha, autor, descripcion, tema)
            )
            self.conn.commit()
            messagebox.showinfo("Éxito", "Link guardado correctamente")
            self.clear_link_form()
            self.load_links()
        except Error as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")

    def update_link(self):
        """Actualiza un link existente"""
        link_id = self.link_id_var.get()

        if not link_id:
            messagebox.showerror("Error", "Seleccione un link para actualizar")
            return

        # Obtener datos del formulario
        if not self.user_combo.get():
            messagebox.showerror("Error", "Debe seleccionar un usuario")
            return

        if not self.multimedia_combo.get():
            messagebox.showerror("Error", "Debe seleccionar un tipo de multimedia")
            return

        link = self.link_entry.get().strip()
        if not link:
            messagebox.showerror("Error", "El campo link es obligatorio")
            return

        # Extraer IDs de las selecciones de combo
        user_id = self.user_combo.get().split(' - ')[0]
        multimedia_id = self.multimedia_combo.get().split(' - ')[0]

        fecha = self.fecha_entry.get().strip()
        autor = self.autor_entry.get().strip()
        descripcion = self.descripcion_text.get("1.0", "end-1c").strip()
        tema = self.tema_entry.get().strip()

        try:
            self.cursor.execute(
                """UPDATE links SET
                   usuario_id = %s, link = %s, multimedia_id = %s,
                   fecha = %s, autor = %s, descripcion = %s, tema = %s
                   WHERE id = %s""",
                (user_id, link, multimedia_id, fecha, autor, descripcion, tema, link_id)
            )
            self.conn.commit()

            if self.cursor.rowcount == 0:
                messagebox.showerror("Error", "Link no encontrado")
                return

            messagebox.showinfo("Éxito", "Link actualizado correctamente")
            self.clear_link_form()
            self.load_links()
        except Error as e:
            messagebox.showerror("Error", f"Error al actualizar: {str(e)}")

    def delete_link(self):
        """Elimina un link"""
        link_id = self.link_id_var.get()

        if not link_id:
            messagebox.showerror("Error", "Seleccione un link para eliminar")
            return

        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este link?"):
            return

        try:
            self.cursor.execute("DELETE FROM links WHERE id = %s", (link_id,))
            self.conn.commit()

            if self.cursor.rowcount == 0:
                messagebox.showerror("Error", "Link no encontrado")
                return

            messagebox.showinfo("Éxito", "Link eliminado correctamente")
            self.clear_link_form()
            self.load_links()
        except Error as e:
            messagebox.showerror("Error", f"Error al eliminar: {str(e)}")

    def on_user_select(self, event):
        """Maneja la selección de usuario desde la tabla"""
        selected_item = self.users_table.selection()[0]
        user = self.users_table.item(selected_item, 'values')

        # Llenar el formulario
        self.user_id_entry.delete(0, tk.END)
        self.user_id_entry.insert(0, user[0])

        self.nombre_entry.delete(0, tk.END)
        self.nombre_entry.insert(0, user[1])

        self.apellido_entry.delete(0, tk.END)
        self.apellido_entry.insert(0, user[2])

        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, user[3] if user[3] else "")

    def on_link_select(self, event):
        """Maneja la selección de link desde la tabla"""
        selected_item = self.links_table.selection()
        if not selected_item:
            return

        link_data = self.links_table.item(selected_item[0], 'values')
        link_id = link_data[0]

        # Obtener el registro completo del link desde la base de datos
        self.cursor.execute("""
            SELECT l.id, l.usuario_id, u.nombre, u.apellido, l.link,
                   l.multimedia_id, m.tipo, l.fecha, l.autor,
                   l.descripcion, l.tema
            FROM links l
            JOIN usuario u ON l.usuario_id = u.id
            JOIN multimedia m ON l.multimedia_id = m.id
            WHERE l.id = %s
        """, (link_id,))
        link = self.cursor.fetchone()
        if not link:
            return

        # Establecer el ID de link oculto
        self.link_id_var.set(link[0])

        # Limpiar formulario
        self.clear_link_form()

        # Llenar combos
        user_idx = -1
        for i, user_item in enumerate(self.user_combo['values']):
            if user_item.startswith(link[1]):
                user_idx = i
                break
        if user_idx >= 0:
            self.user_combo.current(user_idx)

        multimedia_idx = -1
        for i, media_item in enumerate(self.multimedia_combo['values']):
            if media_item.startswith(str(link[5])):
                multimedia_idx = i
                break
        if multimedia_idx >= 0:
            self.multimedia_combo.current(multimedia_idx)

        # Llenar el resto del formulario
        self.link_entry.insert(0, link[4])
        self.fecha_entry.insert(0, link[7])
        self.autor_entry.insert(0, link[8] if link[8] else "")
        self.descripcion_text.insert("1.0", link[9] if link[9] else "")
        self.tema_entry.insert(0, link[10] if link[10] else "")

    def clear_user_form(self):
        """Limpia todos los campos en el formulario de usuario"""
        self.user_id_entry.delete(0, tk.END)
        self.nombre_entry.delete(0, tk.END)
        self.apellido_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)

        # Limpiar selección de tabla
        for item in self.users_table.selection():
            self.users_table.selection_remove(item)

    def clear_link_form(self):
        """Limpia todos los campos en el formulario de link"""
        self.user_combo.set('')
        self.multimedia_combo.set('')
        self.link_entry.delete(0, tk.END)
        self.fecha_entry.delete(0, tk.END)
        self.fecha_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.autor_entry.delete(0, tk.END)
        self.descripcion_text.delete("1.0", tk.END)
        self.tema_entry.delete(0, tk.END)
        self.link_id_var.set('')

        # Limpiar selección de tabla
        for item in self.links_table.selection():
            self.links_table.selection_remove(item)


if __name__ == "__main__":
    root = tk.Tk()
    app = LinksDeInteresApp(root)
    root.mainloop()

