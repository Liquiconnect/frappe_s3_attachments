import frappe
import requests
from frappe import _
from frappe.core.doctype.file.file import File
from frappe.core.doctype.file.utils import decode_file_content
from frappe.utils import get_url

class CustomFile(File):
	def get_content(self):
		if self.is_folder:
			frappe.throw(_("Cannot get file contents of a Folder"))

		if self.get("content"):
			self._content = self.content
			if self.decode:
				self._content = decode_file_content(self._content)
				self.decode = False
			# self.content = None # TODO: This needs to happen; make it happen somehow
			return self._content

		# handle file content based on file_url / storage
		if self.file_url:
			self.validate_file_url()

			if "/api/method/frappe_s3_attachment.controller.generate_file" in self.file_url:
				return self._get_private_file_content()

			if self.file_url.startswith("http://") or self.file_url.startswith("https://"):
				return self._get_public_file_content()

		# fallback: local filesystem
		self._get_local_file_content()
		return super().get_content()

	
	def _get_public_file_content(self) -> bytes:
		try:
			response = requests.get(self.file_url, timeout=20)
			response.raise_for_status()
			return response.content
		except Exception as e:
			frappe.throw(f"Unable to download public file: {str(e)}")


	def _get_private_file_content(self) -> bytes:
		try:
			url = get_url() + self.file_url
			cookies = getattr(frappe.request, "cookies", {})
			response = requests.get(url, cookies=cookies, timeout=30)
			response.raise_for_status()
			return response.content
		except Exception as e:
			frappe.throw(f"Unable to download private file: {str(e)}")


	def _get_local_file_content(self) -> bytes:
		file_path = self.get_full_path()
		with open(file_path, "rb") as f:
			content = f.read()
			try:
				return content.decode()
			except UnicodeDecodeError:
				return content
